import pandas as pd

jobs = [
{
"title":"Director Global Engagement",
"organization":"University of Washington",
"location":"Seattle",
"salary":"$120k",
"match_score":92,
"link":"https://www.washington.edu/jobs/"
},
{
"title":"Assistant Director Study Abroad",
"organization":"University of Hawaii",
"location":"Honolulu",
"salary":"$115k",
"match_score":88,
"link":"https://www.governmentjobs.com/"
},
{
"title":"Director International Programs",
"organization":"HigherEdJobs listing",
"location":"Remote",
"salary":"$118k",
"match_score":85,
"link":"https://www.higheredjobs.com/"
}
]

df = pd.DataFrame(jobs)

df.to_csv("jobs.csv",index=False)
