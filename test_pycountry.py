# test_pycountry.py
import pycountry

# Test getting country by code
india = pycountry.countries.get(alpha_2='IN')
print(f"Country: {india.name}")  # Should print: India

# Test getting all countries
print(f"Total countries: {len(pycountry.countries)}")