from kavach.lambda_handler import ingest_handler


def test_ingest_handler_runs_without_dynamodb_configured():
    result = ingest_handler({})
    assert result["statusCode"] == 200
