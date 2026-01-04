import azure.functions as func
import json
from balance_logic import get_all_balances_by_date

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.function_name(name="token_balances")
@app.route(route="token_balances", auth_level=func.AuthLevel.FUNCTION)
def main(req: func.HttpRequest) -> func.HttpResponse:
    date = req.params.get("date")
    if not date:
        return func.HttpResponse("Missing 'date' query parameter in YYYY-MM-DD format", status_code=400)

    try:
        data = get_all_balances_by_date(date)
        return func.HttpResponse(json.dumps(data, indent=2), mimetype="application/json")
    except Exception as e:
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
