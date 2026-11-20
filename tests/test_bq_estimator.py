from google.api_core.exceptions import BadRequest
from google.auth.exceptions import DefaultCredentialsError

from bq_cost_guard.bq_estimator import TIB, estimate


def test_cost(mocker):
    client = mocker.Mock()
    client.query.return_value.total_bytes_processed = TIB
    est = estimate(client, "SELECT 1", 6.25)
    assert (est.bytes_processed, est.cost_usd, est.error) == (TIB, 6.25, None)
    config = client.query.call_args.kwargs["job_config"]
    assert config.dry_run is True and config.use_query_cache is False


def test_syntax_error_does_not_raise(mocker):
    client = mocker.Mock()
    client.query.side_effect = BadRequest("Syntax error")
    est = estimate(client, "SELEC", 6.25)
    assert est.cost_usd is None and "Syntax error" in est.error


def test_auth_error_does_not_raise(mocker):
    client = mocker.Mock()
    client.query.side_effect = DefaultCredentialsError("no creds")
    assert "no creds" in estimate(client, "SELECT 1", 6.25).error
