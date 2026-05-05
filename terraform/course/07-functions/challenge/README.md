# Challenge — Functions

## Build It Yourself

Using ONLY the `local` provider and built-in functions, create a configuration that:

1. Takes a variable `raw_csv` (string) containing CSV data:
   ```
   name,role,team
   alice,developer,backend
   bob,designer,frontend
   charlie,devops,platform
   dave,developer,backend
   eve,manager,platform
   ```

2. Uses functions to:
   - Parse the CSV into a list of objects using `csvdecode()`
   - Extract unique teams using `distinct()` and `for` expressions
   - Count members per team
   - Find all developers (filter by role)
   - Create an uppercase version of all names
   - Generate a JSON report of the parsed data

3. Writes three output files:
   - `output/team-report.txt` — team names and member counts
   - `output/developers.txt` — list of developers only
   - `output/data.json` — full parsed data as JSON

4. Outputs:
   - `unique_teams` — list of unique team names
   - `developer_count` — number of developers
   - `team_sizes` — map of team name → member count

## Functions You'll Need
`csvdecode`, `distinct`, `length`, `upper`, `jsonencode`, `join`, `formatdate`, `timestamp`

## Verify
```bash
terraform init
terraform apply -auto-approve
cat output/team-report.txt
cat output/data.json
terraform output -json
```
