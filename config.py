# User:pass for simplify.jobs account
USERNAME = 'biharer614@ekposta.com'
PASSWORD = 'biharer614@ekposta.com'

# Parameters of the database
# Feel free to login to the database end explore its' structure
DB_PARAMS = {
    'dbname': 'simplify',
    'user': 'simplifyuser',
    'password': 'simplifyjobs',
    'host': '107.189.17.3'
}

# Query for inserting data into database
INSERT_DATA_QUERY = """
   INSERT INTO job_offers (
       id, position_name, company_name, locations, experience_level,
       desired_skills, categories, employee_count, company_website,
       company_stage, company_funding, foundation_year, company_industries
   ) VALUES (
       %(id)s, %(position_name)s, %(company_name)s, %(locations)s, %(experience_level)s,
       %(desired_skills)s, %(categories)s, %(employee_count)s, %(company_website)s,
       %(company_stage)s, %(company_funding)s, %(foundation_year)s, %(company_industries)s
   )
"""
