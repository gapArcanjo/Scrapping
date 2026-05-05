from handlers import generate_monthly_health_report


def test_generate_monthly_health_report_returns_message():
    assert generate_monthly_health_report() == "Monthly health report generated."
