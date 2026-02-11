
import pandas as pd
url_base = "https://public.opendatasoft.com/api/records/1.0/search/?dataset=geonames-all-cities-with-a-population-1000&q=population>20000&rows=1000&refine.country_code=FR"

df = pd.DataFrame(url_base)