"""Full-pipeline snapshot regression test."""


def test_full_schema_snapshot(ocx_model, data_regression):
    data_regression.check(ocx_model.model_dump(mode="json"))
