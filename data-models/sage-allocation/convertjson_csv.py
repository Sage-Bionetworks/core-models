import pandas as pd
import json

# Sample JSON data
data = {
    "employees": [
        {"name": "John Doe", "age": 30, "department": "IT"},
        {"name": "Jane Smith", "age": 25, "department": "HR"},
        {"name": "Sam Brown", "age": 35, "department": "Finance"}
    ]
}

# Convert JSON to DataFrame
df = pd.DataFrame(data["employees"])

# Save DataFrame to CSV
df.to_csv("output.csv", index=False)

# Print DataFrame to verify
print(df)
