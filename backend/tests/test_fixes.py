"""
Tests that verify all performance and correctness fixes applied to the
خطة التطوير (plan) page backend.

Fix coverage:
  1. _parse_embedding       — correct string/list/array handling
  2. Vectorized similarity  — matrix dot-product matches old scalar loop
  3. analyze_gap parallel   — 3 DB fetches run concurrently, not serially
  4. add_student_courses    — single batch SELECT instead of N SELECTs (N+1 fix)
  5. add_extra_skills       — batch INSERT via execute_values instead of N INSERTs
  6. process_job/course     — conn.commit() called once per batch, not per skill
"""

import sys
import os
import time
import numpy as np
import pytest
from unittest.mock import MagicMock, patch, call

# ── Path setup ──────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock heavy ML dependency before any backend module is imported so the
# SentenceTransformer model is never actually loaded during tests.
_mock_st_module = MagicMock()
_mock_st_model = MagicMock()
_mock_st_model.encode.return_value = np.zeros(384).tolist()
_mock_st_module.SentenceTransformer.return_value = _mock_st_model
sys.modules.setdefault("sentence_transformers", _mock_st_module)

# Also mock anthropic to avoid API key checks at import time
sys.modules.setdefault("anthropic", MagicMock())
sys.modules.setdefault("pdfplumber", MagicMock())


# ════════════════════════════════════════════════════════════════════════════
# Fix 1 — _parse_embedding
# ════════════════════════════════════════════════════════════════════════════

class TestParseEmbedding:
    """_parse_embedding must handle every format the DB can return."""

    def setup_method(self):
        from core.gap_analyzer import _parse_embedding
        self.parse = _parse_embedding

    def test_string_input_returns_ndarray(self):
        result = self.parse("[1.0, 2.5, -0.3]")
        assert isinstance(result, np.ndarray)
        np.testing.assert_allclose(result, [1.0, 2.5, -0.3])

    def test_list_input_returns_ndarray(self):
        result = self.parse([1.0, 2.0, 3.0])
        assert isinstance(result, np.ndarray)
        np.testing.assert_allclose(result, [1.0, 2.0, 3.0])

    def test_numpy_input_passes_through(self):
        arr = np.array([0.1, 0.2, 0.3])
        result = self.parse(arr)
        assert isinstance(result, np.ndarray)
        np.testing.assert_allclose(result, arr)

    def test_dtype_is_float(self):
        result = self.parse("[1, 2, 3]")
        assert result.dtype == float

    def test_integer_list_converted_to_float(self):
        result = self.parse([1, 0, -1])
        assert result.dtype == float
        np.testing.assert_allclose(result, [1.0, 0.0, -1.0])


# ════════════════════════════════════════════════════════════════════════════
# Fix 2 — Vectorized cosine similarity
# ════════════════════════════════════════════════════════════════════════════

class TestVectorizedSimilarity:
    """
    The new analyze_gap path uses S_norm @ j_unit instead of a Python loop
    over cosine_similarity(). Both must produce identical results.
    """

    def setup_method(self):
        from core.gap_analyzer import cosine_similarity, _parse_embedding
        self.scalar_sim = cosine_similarity
        self.parse = _parse_embedding
        np.random.seed(42)

    def _vectorized_sims(self, student_vecs, job_vec):
        """Exact replication of the new analyze_gap vectorization logic."""
        S = np.array(student_vecs, dtype=float)
        s_norms = np.linalg.norm(S, axis=1, keepdims=True)
        s_norms[s_norms == 0] = 1.0
        S_norm = S / s_norms
        j_norm = np.linalg.norm(job_vec)
        j_unit = job_vec / j_norm if j_norm > 0 else job_vec
        return S_norm @ j_unit

    def test_matches_scalar_on_random_vectors(self):
        vecs = [np.random.rand(384) for _ in range(20)]
        job = np.random.rand(384)
        scalar = [self.scalar_sim(job, v) for v in vecs]
        vector = self._vectorized_sims(vecs, job)
        np.testing.assert_allclose(scalar, vector, rtol=1e-5)

    def test_identical_vectors_score_one(self):
        v = np.random.rand(384)
        sims = self._vectorized_sims([v], v)
        assert abs(sims[0] - 1.0) < 1e-6

    def test_orthogonal_vectors_score_zero(self):
        v1, v2 = np.zeros(384), np.zeros(384)
        v1[0] = 1.0
        v2[1] = 1.0
        sims = self._vectorized_sims([v2], v1)
        assert abs(sims[0]) < 1e-6

    def test_best_match_index_same_as_scalar(self):
        vecs = [np.random.rand(384) for _ in range(50)]
        job = np.random.rand(384)
        scalar_best = int(np.argmax([self.scalar_sim(job, v) for v in vecs]))
        vector_best = int(np.argmax(self._vectorized_sims(vecs, job)))
        assert scalar_best == vector_best

    def test_scores_bounded_minus_one_to_one(self):
        vecs = [np.random.rand(384) for _ in range(100)]
        job = np.random.rand(384)
        sims = self._vectorized_sims(vecs, job)
        assert np.all(sims >= -1.0 - 1e-9)
        assert np.all(sims <= 1.0 + 1e-9)


# ════════════════════════════════════════════════════════════════════════════
# Fix 3 — analyze_gap parallel execution
# ════════════════════════════════════════════════════════════════════════════

class TestAnalyzeGapParallel:

    def test_all_three_fetch_functions_are_called(self):
        from core.gap_analyzer import analyze_gap
        with (
            patch("core.gap_analyzer.get_student_skills", return_value=[]) as m_s,
            patch("core.gap_analyzer.get_job_skills",     return_value=[]) as m_j,
            patch("core.gap_analyzer.get_tfidf_weights",  return_value={}) as m_t,
        ):
            analyze_gap(1, 1)
        m_s.assert_called_once_with(1)
        m_j.assert_called_once_with(1)
        m_t.assert_called_once()

    def test_parallel_faster_than_serial(self):
        """
        Each fetch sleeps 100 ms to simulate DB latency.
        Parallel execution should finish in ~130 ms, not ~300 ms.
        """
        from core.gap_analyzer import analyze_gap

        def slow(_=None):
            time.sleep(0.1)
            return []

        with (
            patch("core.gap_analyzer.get_student_skills", side_effect=slow),
            patch("core.gap_analyzer.get_job_skills",     side_effect=slow),
            patch("core.gap_analyzer.get_tfidf_weights",  side_effect=slow),
        ):
            t0 = time.perf_counter()
            analyze_gap(1, 1)
            elapsed = time.perf_counter() - t0

        assert elapsed < 0.25, (
            f"Fetches appear sequential (took {elapsed:.3f}s); "
            "expected parallel execution under 250ms"
        )

    def test_empty_job_skills_returns_zero_score(self):
        from core.gap_analyzer import analyze_gap
        with (
            patch("core.gap_analyzer.get_student_skills", return_value=[]),
            patch("core.gap_analyzer.get_job_skills",     return_value=[]),
            patch("core.gap_analyzer.get_tfidf_weights",  return_value={}),
        ):
            result = analyze_gap(1, 1)
        assert result["readiness_score"] == 0
        assert result["total_job_skills"] == 0

    def test_no_student_skills_returns_error_key(self):
        from core.gap_analyzer import analyze_gap
        job_skill = {
            "id": 1, "name": "Python", "category": "technical",
            "embedding": [0.1] * 384, "weight": 1.0, "is_required": True,
        }
        with (
            patch("core.gap_analyzer.get_student_skills", return_value=[]),
            patch("core.gap_analyzer.get_job_skills",     return_value=[job_skill]),
            patch("core.gap_analyzer.get_tfidf_weights",  return_value={}),
        ):
            result = analyze_gap(1, 1)
        assert "error" in result

    def test_identical_embedding_lands_in_matched_skills(self):
        from core.gap_analyzer import analyze_gap
        np.random.seed(7)
        emb = np.random.rand(384).tolist()
        student = {
            "id": 10, "name": "Python", "category": "technical",
            "embedding": emb, "confidence": 1.0, "source": "course",
        }
        job = {
            "id": 20, "name": "Python", "category": "technical",
            "embedding": emb, "weight": 1.0, "is_required": True,
        }
        with (
            patch("core.gap_analyzer.get_student_skills", return_value=[student]),
            patch("core.gap_analyzer.get_job_skills",     return_value=[job]),
            patch("core.gap_analyzer.get_tfidf_weights",  return_value={20: 1.0}),
        ):
            result = analyze_gap(1, 1)
        assert result["matched_count"] == 1
        assert result["matched_skills"][0]["skill"] == "Python"
        assert result["readiness_score"] > 0

    def test_orthogonal_embedding_lands_in_missing_skills(self):
        from core.gap_analyzer import analyze_gap
        v_student, v_job = np.zeros(384), np.zeros(384)
        v_student[0] = 1.0
        v_job[1] = 1.0
        student = {
            "id": 10, "name": "Skill A", "category": "technical",
            "embedding": v_student.tolist(), "confidence": 1.0, "source": "course",
        }
        job = {
            "id": 20, "name": "Skill B", "category": "technical",
            "embedding": v_job.tolist(), "weight": 1.0, "is_required": True,
        }
        with (
            patch("core.gap_analyzer.get_student_skills", return_value=[student]),
            patch("core.gap_analyzer.get_job_skills",     return_value=[job]),
            patch("core.gap_analyzer.get_tfidf_weights",  return_value={20: 1.0}),
        ):
            result = analyze_gap(1, 1)
        assert result["missing_count"] == 1
        assert result["matched_count"] == 0


# ════════════════════════════════════════════════════════════════════════════
# Fix 4 — add_student_courses: batch SELECT (N+1 fix)
# ════════════════════════════════════════════════════════════════════════════

class TestAddStudentCoursesBatch:

    def _make_db(self, found_rows):
        cursor = MagicMock()
        cursor.fetchall.return_value = found_rows
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return conn, cursor

    def test_single_select_for_multiple_courses(self):
        """N courses → exactly 1 SELECT with ANY(), not N individual SELECTs."""
        conn, cursor = self._make_db([
            {"course_code": "CS101", "id": 1},
            {"course_code": "CS102", "id": 2},
        ])
        with patch("api.routes.student.get_connection", return_value=conn):
            from api.routes.student import add_student_courses, CourseAdd
            add_student_courses(1, CourseAdd(course_codes=["CS101", "CS102", "CS999"]))

        any_selects = [c for c in cursor.execute.call_args_list if "ANY" in str(c)]
        assert len(any_selects) == 1, (
            f"Expected 1 batch SELECT but got {len(any_selects)} — N+1 bug still present"
        )

    def test_added_and_not_found_split_correctly(self):
        conn, cursor = self._make_db([{"course_code": "CS101", "id": 1}])
        with patch("api.routes.student.get_connection", return_value=conn):
            from api.routes.student import add_student_courses, CourseAdd
            result = add_student_courses(1, CourseAdd(course_codes=["CS101", "CS999"]))

        assert result["count"] == 1
        assert "CS101" in result["added_courses"]
        assert "CS999" in result["not_found"]

    def test_empty_course_list_issues_no_queries(self):
        conn, cursor = self._make_db([])
        with patch("api.routes.student.get_connection", return_value=conn):
            from api.routes.student import add_student_courses, CourseAdd
            result = add_student_courses(1, CourseAdd(course_codes=[]))

        cursor.execute.assert_not_called()
        assert result["count"] == 0

    def test_no_cache_invalidation_when_nothing_added(self):
        """DELETE readiness_scores must NOT fire when all codes are unknown."""
        conn, cursor = self._make_db([])
        with patch("api.routes.student.get_connection", return_value=conn):
            from api.routes.student import add_student_courses, CourseAdd
            add_student_courses(1, CourseAdd(course_codes=["NOTEXIST"]))

        delete_calls = [c for c in cursor.execute.call_args_list if "DELETE" in str(c)]
        assert len(delete_calls) == 0

    def test_cache_invalidated_when_courses_added(self):
        """DELETE readiness_scores MUST fire when at least one course was added."""
        conn, cursor = self._make_db([{"course_code": "CS101", "id": 1}])
        with patch("api.routes.student.get_connection", return_value=conn):
            from api.routes.student import add_student_courses, CourseAdd
            add_student_courses(1, CourseAdd(course_codes=["CS101"]))

        delete_calls = [c for c in cursor.execute.call_args_list if "DELETE" in str(c)]
        assert len(delete_calls) == 1


# ════════════════════════════════════════════════════════════════════════════
# Fix 5 — add_extra_skills: batch INSERT via execute_values
# ════════════════════════════════════════════════════════════════════════════

class TestAddExtraSkillsBatch:

    def _make_db(self, valid_ids):
        cursor = MagicMock()
        cursor.fetchall.return_value = [{"id": i} for i in valid_ids]
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return conn, cursor

    def test_execute_values_called_once_for_all_skills(self):
        conn, cursor = self._make_db([1, 2, 3])
        with (
            patch("api.routes.student.get_connection", return_value=conn),
            patch("psycopg2.extras.execute_values") as mock_ev,
        ):
            from api.routes.student import add_extra_skills, BulkSkillAdd
            result = add_extra_skills(
                1, BulkSkillAdd(skill_ids=[1, 2, 3], proficiency=4, source="self_reported")
            )
        mock_ev.assert_called_once()
        assert result["added"] == 3

    def test_invalid_skill_ids_excluded_from_insert(self):
        conn, cursor = self._make_db([1, 3])  # 2 and 99 don't exist
        with (
            patch("api.routes.student.get_connection", return_value=conn),
            patch("psycopg2.extras.execute_values") as mock_ev,
        ):
            from api.routes.student import add_extra_skills, BulkSkillAdd
            result = add_extra_skills(
                1, BulkSkillAdd(skill_ids=[1, 2, 3, 99], proficiency=4, source="self_reported")
            )
        assert result["added"] == 2
        inserted_ids = {row[1] for row in mock_ev.call_args[0][2]}
        assert 2 not in inserted_ids
        assert 99 not in inserted_ids

    def test_no_insert_when_all_ids_invalid(self):
        conn, cursor = self._make_db([])
        with (
            patch("api.routes.student.get_connection", return_value=conn),
            patch("psycopg2.extras.execute_values") as mock_ev,
        ):
            from api.routes.student import add_extra_skills, BulkSkillAdd
            result = add_extra_skills(
                1, BulkSkillAdd(skill_ids=[999], proficiency=4, source="self_reported")
            )
        mock_ev.assert_not_called()
        assert result["added"] == 0

    def test_single_select_regardless_of_input_size(self):
        """Validation uses one ANY() query even for 50 IDs."""
        conn, cursor = self._make_db(list(range(1, 51)))
        with (
            patch("api.routes.student.get_connection", return_value=conn),
            patch("psycopg2.extras.execute_values"),
        ):
            from api.routes.student import add_extra_skills, BulkSkillAdd
            add_extra_skills(
                1, BulkSkillAdd(skill_ids=list(range(1, 51)), proficiency=4, source="test")
            )
        any_selects = [c for c in cursor.execute.call_args_list if "ANY" in str(c)]
        assert len(any_selects) == 1, (
            f"Expected 1 batch SELECT but got {len(any_selects)}"
        )

    def test_proficiency_and_source_passed_to_insert(self):
        conn, cursor = self._make_db([7])
        with (
            patch("api.routes.student.get_connection", return_value=conn),
            patch("psycopg2.extras.execute_values") as mock_ev,
        ):
            from api.routes.student import add_extra_skills, BulkSkillAdd
            add_extra_skills(
                1, BulkSkillAdd(skill_ids=[7], proficiency=5, source="internship")
            )
        rows = mock_ev.call_args[0][2]
        student_id, skill_id, proficiency, source = rows[0]
        assert proficiency == 5
        assert source == "internship"
        assert skill_id == 7


# ════════════════════════════════════════════════════════════════════════════
# Fix 6 — skill_extractor: commit once per batch, not per skill
# ════════════════════════════════════════════════════════════════════════════

class TestSkillExtractorCommitOnce:

    def _make_db(self):
        cursor = MagicMock()
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return conn, cursor

    def _fake_skills(self, names):
        return [{"name": n, "type": "technical", "confidence": 0.9} for n in names]

    def test_process_job_commits_once_for_multiple_skills(self):
        conn, _ = self._make_db()
        skills = self._fake_skills(["Python", "SQL", "Docker", "FastAPI", "Redis"])

        with (
            patch("core.skill_extractor.get_connection", return_value=conn),
            patch("core.skill_extractor.extract_skills_from_text", return_value=skills),
            patch("core.skill_extractor.get_or_create_skill", side_effect=list(range(1, 20))),
        ):
            from core.skill_extractor import process_job
            process_job(1, "Backend Dev", "Python FastAPI SQL Docker Redis")

        assert conn.commit.call_count == 1, (
            f"commit called {conn.commit.call_count} times — commit-in-loop bug still present"
        )

    def test_process_course_commits_once_for_multiple_skills(self):
        conn, _ = self._make_db()
        skills = self._fake_skills(["Python", "Data Structures", "Algorithms"])

        with (
            patch("core.skill_extractor.get_connection", return_value=conn),
            patch("core.skill_extractor.extract_skills_from_text", return_value=skills),
            patch("core.skill_extractor.get_or_create_skill", side_effect=list(range(1, 20))),
        ):
            from core.skill_extractor import process_course
            process_course(1, "CS101", "Intro to CS", "description", "outcomes")

        assert conn.commit.call_count == 1, (
            f"commit called {conn.commit.call_count} times — commit-in-loop bug still present"
        )

    def test_process_job_commit_count_does_not_grow_with_skill_count(self):
        """Verify commit is O(1) not O(n) — commit count must stay 1 for 10 skills."""
        conn, _ = self._make_db()
        skills = self._fake_skills([f"Skill{i}" for i in range(10)])

        with (
            patch("core.skill_extractor.get_connection", return_value=conn),
            patch("core.skill_extractor.extract_skills_from_text", return_value=skills),
            patch("core.skill_extractor.get_or_create_skill", side_effect=list(range(1, 20))),
        ):
            from core.skill_extractor import process_job
            process_job(1, "Big Job", "lots of skills")

        assert conn.commit.call_count == 1, (
            f"Expected 1 commit for 10 skills but got {conn.commit.call_count}"
        )

    def test_process_job_no_skills_still_commits_once(self):
        conn, _ = self._make_db()

        with (
            patch("core.skill_extractor.get_connection", return_value=conn),
            patch("core.skill_extractor.extract_skills_from_text", return_value=[]),
        ):
            from core.skill_extractor import process_job
            process_job(1, "Empty Job", "no skills here")

        assert conn.commit.call_count == 1
