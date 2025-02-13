import pandas as pd
import json

# Sample JSON data
data = {
"jobRoles": {
          "Science and Data Biomedical Data Manager ": "XL",
          "Science and Data Scientific Community Manager": "M",
          "Governance Innovation Associate Director": "M",
          "Governance Innovation Privacy and Data Protection Analyst": "XL",
          "Governance Innovation Technical Program Manager": "M",
          "Technology Front End Software Engineer": "S",
          "Technology Back End Software Engineer": "S",
          "Technology Product Manager": "XXS",
          "Technology Technical Program Manager": "XS",
          "Technology Associate Director": "XXS",
          "Science and Data Bioinformatics Engineer": "?",
          "Science and Data Associate Director": "?"
        }
}

# Convert JSON to DataFrame
df = pd.DataFrame(data["jobRoles"])

# Save DataFrame to CSV
df.to_csv("output.csv", index=False)

# Print DataFrame to verify
print(df)
