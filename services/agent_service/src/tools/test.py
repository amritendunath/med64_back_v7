import requests

def doctor_info(hospital_name):

    try:
        # Format the API URL
        base_url = "http://localhost:7001"
        endpoint = f"/doctor"
        api_url = base_url + endpoint
        params = {

            'hospital_name': hospital_name
        }

        # Make GET request to the API
        response = requests.get(api_url, params=params)
        # Check if request was successful
        response.raise_for_status()
        # Parse the response
        data = response.json()
        return data

    except requests.exceptions.RequestException as e:
        return f"Error checking availability: {str(e)}"
    
if __name__ == "__main__":
    result2 = doctor_info("chaitanya hospital")
    print(result2)
