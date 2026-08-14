Note : I just want to add that this entire file text is hand-written . It looks highly polished and presented as I wanted the file to be readable at the end. However the actual content was hand written by me in a notepad first and then used a tool to convert it into a markdown file friendly format.

What I built
------------

I built a pipeline that takes three source files (A, B, and C) containing medical claims data plus a dictionary of diagnosis codes and merges them into one single unified table.

The pipeline I built has 9 stages, each stage with clear logs on what changes have been done and what happened to the data in each stage (rows in, rows out, no of rows dropped, reason). A gist of what each stage does is given below. _(Wanted to elaborate on this more extensively but because of length requirements made this concise. I am ready to elaborate on this further in any follow up conversations.)_

*   **Stage 1 - Ingest:** This stage just loads the four raw files exactly as they are without making any changes. This gives me a starting point which future stages can compare against.
    
*   **Stage 2 - Select and rename columns:** This stage renames every column to one common set of names (the target column list that we need) and also removes any other columns that are not part of the target output list (Ex: facility type/claim type). So after this step all the three sources will look structurally similar.
    
*   **Stage 3 - Reshape:** This stage brings 8 different diagnosis columns of Source A into separate rows and also keeps only the latest version claim in Source C. Then it splits Source C delimited string into separate rows. No changes were made to Source B as it was already structurally correct.
    
*   **Stage 4 - Normalize:** Implemented separate functions to make sure values in all three sources follow the correct format (diagnosis code - only Uppercase and no dots, date - YYYY-MM-DD, gender - M/F only).
    
*   **Stage 5 - Filter:** This stage does two things mainly. Removes the rows with missing patient\_id and also removes rows outside the allowed date range (2018-01-01 to 2025-02-28).
    
*   **Stage 6 - Combine:** This stage stacks the three tables into one single unified table.
    
*   **Stage 7 - Deduplicate:** This stage removes any row that is the duplicate of another on (source, claim, diagnosis code) and returns the updated dataframe.
    
*   **Stage 8 - Dictionary join:** This stage adds the description for each diagnosis from the dictionary to the main combined dataframe. It is joined by matching each row’s diagnosis code to the dictionary.
    
*   **Stage 9 - Validate:** This stage runs the 10 required checks (row counts, distinct patients/claims/codes, formatting rules, and a check that running the whole pipeline twice gives identical results) and reports a clear pass/fail for each.
    

Apart from this, I also built a small API with 4 endpoints using FastAPI:

*   POST /run - To trigger a run
    
*   GET /run/{id}/stages - To view the stage-by-stage breakdown
    
*   GET /run/{id}/validate - To view the validation results
    
*   GET /summary - For a summary
    

I also built a simple webpage with a button that calls these endpoints and displays the results as tables.

What problem it solves
----------------------

The main problem my pipeline solves is that all the three source files represent the same thing, which is medical claims and their diagnoses, but all three of them store it differently, making it impossible to unify them together.

### Different shapes for same data:

*   **Source A** has 8 diagnosis slots per claim in each row, so one row per claim.
    
*   **Source B** has only one diagnosis per row, so multiple rows are possible for each claim.
    
*   **Source C** stores all diagnoses for a claim in a single cell in a pipe-delimited string. Also, Source C has multiple rows per claim through a versions column.
    

### Different columns names used for the same thing:

*   **Patient ID** was patient\_id in A, member\_id in B, and pt\_ref in C.
    
*   **Claim ID** was claim\_id in A, encounter\_id in B, and claim\_ref in C.
    
*   Apart from this, there were many extra columns which were not required in the target output, like facility type, claim type, etc.
    

### Different values for the same thing (Gender, service date and diagnosis codes):

*   **Gender** was M/F in Source A, 1/2 in B, and Male/Female in C.
    
*   **Service date** was a plain integer in A (Ex: 20231002) but the correct format in B and C.
    
*   **Diagnosis code** was dotted in A (E03.9) and dotted plus lowercase (h25.13) in C.
    

What I had to reconcile
-----------------------

*   I had to rename every column name into a single set of shared column names.
    
*   I had to also reshape A and C so that every source had a separate row for each diagnosis.
    
*   I had to fix the gender, service\_date, and diagnosis formatting so the values looked identical across all the sources.
    

What would have gone wrong if I had simply combined them as they came?
----------------------------------------------------------------------

*   The columns which mean the same thing would end up as separate columns - think patient\_id, member\_id, and pt\_ref as three separate columns instead of one.
    
*   The data would be very inconsistent. Some rows will have only single diagnoses, some rows will have all the diagnoses of the claim in the row itself.
    
*   Moreover, Source C older versions would get counted as separate claims. This will make diagnosis counts and row counts meaningless.
    
*   Counting distinct diagnoses would be impossible because E03.9, e03.9, and E039 would all be counted as different diagnoses, which they are not. They are exactly the same but they are differently formatted, that's it.
    
*   Also, gender and dates would be inconsistent, and the rules in the requirement could not have been followed.
    

Why I did it that way
---------------------

*   **I normalized before the deduplication step:** I followed this order because if I didn't normalize the differently formatted diagnosis codes (I25.10 vs i2510) they would not have counted as duplicates even if all the other column values were duplicates during the deduplication step. However, there was no real case of this in the data, but I did it anyway as a good practice for other datasets that could have this issue.
    
*   **I kept only the latest version for each claim in Source C:** In Source C, some claims had multiple versions. I decided to keep the latest version only and drop other rows as earlier versions are not separate events and the final version is generally the one that is required. Keeping all versions would have double-counted the claims, leading to wrong data.
    
*   **I handled codes missing from the dictionary:** The dictionary had only 40 codes, but my final combined dataframe had 44. So 4 codes did not have a description in the dictionary. Instead of dropping them, I just labeled them with “UNKNOWN DIAGNOSIS” for the description because dropping them blocked me from reaching the required row count.
    
*   **Gender mapping for Source B:** This was something I just did from assumption. There is no key which tells 1 equals Male and 2 equals Female. I just couldn’t verify this from the files given. However, I decided to proceed with this mapping.
    
*   **Deduplication step:** I removed duplicates on the grain (SRC, CLAIM\_ID, and DIAGNOSIS\_CODE) and did not compare every column as this is what the target table needs. Two rows could differ in other columns and still represent the same claim and diagnosis pair. When duplicates were found, I kept the first occurrence only and dropped the rest. I checked and found every duplicate group was identical across all columns anyway, so keeping the second or third would’ve given the same result here, but then a different dataset might not be so clean. As a result, I specifically kept the first occurrence only.
    

What went wrong along the way
-----------------------------

My reproducibility check in check 10 had two silent bugs that I didn’t catch right away.

First, the run\_pipeline() function returns two things (the dataframe and the stage log), but I called it into only one variable (final\_run2 = run\_pipeline() instead of final\_run2, \_ = run\_pipeline()).

Also, I first didn’t understand the usage of .sort\_values() and .reset\_index() in this part, as I was not aware that the group by operations done in the middle stages will lead to different ordering of rows. Also, I called .sort\_values() and .reset\_index() without reassigning them to variables. I thought these methods would operate directly on the dataframes.

Apart from this, I made smaller mistakes like mismatching filenames inside my code compared to actual names, missing import issues, and also was not aware FastAPI static file server serves only files named exactly index.html while I named mine static.html.

**Honest note:** I used AI extensively for the core logic part as I was not aware of a lot of Pandas operations and methods that were required. As a result, I did not run into core logic failures during actual runs and most issues I ran into were environment problems. However, I tried hand-coding the parts which I didn’t understand at the start, like the reproducibility checks, and hence ran into the above specified issues. Also, before integrating every step of code, I made sure that I understand each line of code and traced the logic step by step, and I’m ready to defend my understanding in a live environment. For the frontend as well I used AI extensively.

However, the backend endpoints written were entirely hand-coded.

What I was unsure about
-----------------------

*   Firstly, I took some time to understand the dataset itself. I did not understand each column, what a claim exactly was, and the real-world relevance. However, I took time and I learnt what each and every column actually means.
    
*   Also, I assumed the mapping for Male/Female to be 1 and 2 for Source B in one of the intermediate steps.
    
*   I was also very unsure about certain operations why they were required like the previous reproducibility check part and also many important pandas functions like .melt(), .loc(), .explode() etc and particularly during the reshaping stages.
    
*   I would surely ask the team for more exact mappings on the genders and also any exact outputs needed for dictionary codes not available in the dictionary.
    

What I would do differently
---------------------------

*   While I finished everything that was required, I could surely improve on making this pipeline more robust by testing against different kinds of datasets with different issues.
    
*   If this data were a hundred times larger, it would surely bring up more variety of data and hence a variety of new issues for which the pipeline should be updated with new stages and new rules. But apart from this, Pandas loads everything into RAM so a 100 times larger dataset would cause the pipeline to crash from running out of RAM.In this case the pipeline should be rewritten to handle data by chunking in small segments rather than processing the data as a whole.