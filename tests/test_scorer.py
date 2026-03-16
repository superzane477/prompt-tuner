from prompt_tuner.runner import RunResult
from prompt_tuner.scorer import Scorer, score_by_rules, _average_criteria, _weighted_total


class TestRuleScoring:
    def test_good_length(self):
        r = RunResult(prompt="test", model="m", output="x" * 100)
        scores = score_by_rules(r)
        assert scores["length"] == 8.0

    def test_short_length(self):
        r = RunResult(prompt="test", model="m", output="short")
        scores = score_by_rules(r)
        assert scores["length"] == 4.0

    def test_structure_with_bullets(self):
        r = RunResult(prompt="test", model="m", output="- item 1\n- item 2\n- item 3")
        scores = score_by_rules(r)
        assert scores["structure"] >= 6.0

    def test_no_structure(self):
        r = RunResult(prompt="test", model="m", output="Just a plain sentence.")
        scores = score_by_rules(r)
        assert scores["structure"] == 3.0

    def test_completeness_single_sentence(self):
        r = RunResult(prompt="test", model="m", output="One sentence only")
        scores = score_by_rules(r)
        assert scores["completeness"] == 4.0

    def test_completeness_medium(self):
        r = RunResult(prompt="test", model="m", output="First point. Second point. Third point.")
        scores = score_by_rules(r)
        assert scores["completeness"] == 7.0

    def test_completeness_many_sentences(self):
        r = RunResult(prompt="test", model="m", output="A. B. C. D. E. F. G.")
        scores = score_by_rules(r)
        assert scores["completeness"] == 9.0

    def test_repetition_no_repeat(self):
        r = RunResult(prompt="test", model="m", output="The quick brown fox jumps over the lazy dog near a river")
        scores = score_by_rules(r)
        assert scores["repetition"] >= 7.0

    def test_repetition_heavy(self):
        r = RunResult(prompt="test", model="m", output="the same thing the same thing the same thing the same thing")
        scores = score_by_rules(r)
        assert scores["repetition"] < 7.0

    def test_formatting_plain(self):
        r = RunResult(prompt="test", model="m", output="Just plain text without any formatting.")
        scores = score_by_rules(r)
        assert scores["formatting"] == 3.0

    def test_formatting_with_code_block(self):
        r = RunResult(prompt="test", model="m", output="Here is code:\n```python\nprint('hi')\n```")
        scores = score_by_rules(r)
        assert scores["formatting"] >= 5.0

    def test_formatting_with_bold(self):
        r = RunResult(prompt="test", model="m", output="This is **important** text.")
        scores = score_by_rules(r)
        assert scores["formatting"] >= 4.5

    def test_formatting_with_heading(self):
        r = RunResult(prompt="test", model="m", output="# Title\nSome content here.")
        scores = score_by_rules(r)
        assert scores["formatting"] >= 4.5

    def test_all_rule_keys_present(self):
        r = RunResult(prompt="test", model="m", output="- bullet. Second sentence. Third one.")
        scores = score_by_rules(r)
        assert set(scores.keys()) == {"length", "structure", "completeness", "repetition", "formatting"}


class TestScorer:
    def test_score_without_ai(self):
        results = [
            RunResult(prompt="p1", model="m1", output="- point 1\n- point 2\n" + "x" * 100),
            RunResult(prompt="p2", model="m1", output="tiny"),
        ]
        scorer = Scorer(client=None)
        scores = scorer.score(results, criteria=["relevance"], judge_models=[])
        assert len(scores) == 2
        assert scores[0].total > scores[1].total

    def test_exclude_self_judge(self):
        results = [RunResult(prompt="p", model="judge-a", output="x" * 100)]
        scorer = Scorer(client=None)
        scores = scorer.score(results, criteria=["relevance"], judge_models=["judge-a", "judge-b"], exclude_self_judge=True)
        assert len(scores) == 1


class TestAverageCriteria:
    def test_average(self):
        all_scores = [{"relevance": 8.0, "accuracy": 6.0}, {"relevance": 6.0, "accuracy": 10.0}]
        avg = _average_criteria(all_scores, ["relevance", "accuracy"])
        assert avg["relevance"] == 7.0
        assert avg["accuracy"] == 8.0

    def test_empty(self):
        avg = _average_criteria([], ["relevance"])
        assert avg["relevance"] == 5.0


class TestWeightedTotal:
    def test_with_explicit_weights(self):
        criteria_scores = {"relevance": 10.0, "accuracy": 6.0}
        rule_scores = {"length": 8.0}
        weights = {"relevance": 3, "accuracy": 2, "length": 1}
        total = _weighted_total(criteria_scores, rule_scores, weights, ["relevance", "accuracy"])
        expected = (10.0 * 3 + 6.0 * 2 + 8.0 * 1) / (3 + 2 + 1)
        assert total == round(expected, 2)

    def test_default_weights_ai_higher(self):
        criteria_scores = {"relevance": 10.0}
        rule_scores = {"length": 4.0}
        total = _weighted_total(criteria_scores, rule_scores, None, ["relevance"])
        expected = (10.0 * 2 + 4.0 * 1) / (2 + 1)
        assert total == round(expected, 2)

    def test_missing_weight_defaults_to_one(self):
        criteria_scores = {"relevance": 8.0}
        rule_scores = {"length": 6.0, "structure": 4.0}
        weights = {"relevance": 3}
        total = _weighted_total(criteria_scores, rule_scores, weights, ["relevance"])
        expected = (8.0 * 3 + 6.0 * 1 + 4.0 * 1) / (3 + 1 + 1)
        assert total == round(expected, 2)

    def test_empty_scores(self):
        assert _weighted_total({}, {}, None, []) == 0.0
