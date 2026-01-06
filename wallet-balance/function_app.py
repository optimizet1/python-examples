import azure.functions as func
import json
from balance_logic import get_all_balances_by_date
from common import get_boolean_from_value, is_date_older_than_cutoff, get_datetime_str_now_pt

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.function_name(name="token_balances")
@app.route(route="token_balances", auth_level=func.AuthLevel.FUNCTION)
def main(req: func.HttpRequest) -> func.HttpResponse:
    date = req.params.get("date")

    if not date:
        return func.HttpResponse("Missing 'date' query parameter. Must be in YYYY-MM-DD format and newer than '2025-12-01.", status_code=400)
   
    if date and len(date) != 10:
        return func.HttpResponse("'date' query parameter must be in YYYY-MM-DD format.", status_code=400)

    # Arbitrary date cutoff date. I don't want to query too far in the past
    if date and is_date_older_than_cutoff(date):
        return func.HttpResponse("'date' query parameter must be in YYYY-MM-DD format and newer than '2025-12-01.", status_code=400)

    try:
        data = {}
        data = get_all_balances_by_date(date)
        
        data["version"] = "v1.0"
        data["date"] = date
        data["now_pt"] = f"{get_datetime_str_now_pt()}"
        return func.HttpResponse(json.dumps(data, indent=2), mimetype="application/json")
    except Exception as e:
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)

