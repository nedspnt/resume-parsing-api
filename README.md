# resume-parsing-api

Resume Parsing API receives a URL for pdf file as an input and returns an extracted information in JSON format.

## Usage
Clone this repository and then run it locally with Docker
```
docker build  -t resume-parsing-image:latest .
docker run -p 5000:5000 resume-parsing-image:latest 
```
URL
```
https://localhost:5000
```

Endpoint
```
POST /parse-resume
```
Parameters
```
url=https://your-online-pdf-file.pdf

OR

file=your-local-file-in-data-folder.pdf
```
You can find a sample resume hosted online using the term search term `"filetype:pdf mockup resume"`. Here are some of the samples
```
https://uploads-ssl.webflow.com/5ddae92de8923593f273a7a6/5df41806a58b621680c6a2a1_Abdul%20Rafay%20%E2%80%93%20Resume.pdf
```
Or you can test with an internal file that is already uploaded into the project directory under `data/` folder. Currently I have `Ned_Jamta_CV_202305.pdf`. To test new file, you need to put a file into `data/` folder, and rebuild Docker image, and rerun.

Sample usage
```
POST https://localhost:5000/parse-resume?file=Ned_Jamta_CV_202305.pdf
```
```
POST https://localhost:5000/parse-resume?url=https://uploads-ssl.webflow.com/5ddae92de8923593f273a7a6/5df41806a58b621680c6a2a1_Abdul%20Rafay%20%E2%80%93%20Resume.pdf
```


Output format in JSON in case return code 200

```
{
    "contact: {
        ...
    },
    "education": {
        ...
    },
    ...
}
```
The output structure is constructed based on sample output in `data/output_sample.json`.

## Goals
- Create highly accurate resume parsing
- Extensibility to new version for new languages
- Handle loads of thousands of resume parsing request per second
- Return the response in 4 seconds

### Phase 1 Objective
Objective of this project is to create the MVP as quickly as possible, and focus less on the accuracy. The priority would be (1) Make it work (2) Make it right (3) Make it fast, respectively.

Making it work means:
- the structure of the ouput is as instructed, assuming it was from software engineer team.
- all the dependencies are well managed - here we use `requirements.txt` and `Dockerfile`
- the script has been successfully deployed and internal user can see the results

Ability to handle load and response quickly will be based on 
(1) Lean code (2) System design. The code for this first version is far from being lean and optimal, however we can discuss system design and how to scale this service with tools such as Kubernetes.

## About accuracy
To quantify accuracy metric, I suggest we use a custom metric as follows:
```
accuracy = weights * LevensteinRatio(predictions, labels)
```
where weights, predictions, and labels are all arrays. LevensteinDistance function quantify an edit distance between prediction and label, for example between extracted name "Lennon" and actual name "John Lennon". This takes 5 alphabets to edit, so that two words are equal. Therefore the Levenstein Raio of this prediction would be 5/8.5 or 58.8%, where 8.5 is an average of length of word of "Lennon" and "John Lennon". If we think the name is very important to overall score, then we can put a high weight.

Then we apply this same concept for other predictions as well, such company names, and so on. However, this scoring method only applies to the content that we all can agree on facts, such as name, university name, company name. Other gray area such as skills, we can other approach, such as `percent_coverage`.
```
percentage_coverage = len([skill for skill in predicted_skill if skill in labeled_skills])
```
However, this also requires labeled data.

The final accuracy can be a function of multiple metric, for example weighted average. Measuring accuracy helps us improve over time.

## Information Extraction Strategies
In order to achieve the goal, which is to create API that response within 4 seconds, we need to avoid excessively sophisicated method that yield a little better result but consumes a lot more computational resources.

**Strategy 1 : <br>
To split texts into sections, we don't need NLP models, we can use simple text spliting.**

Avoid going through all the strings for all tasks is the first priority for information extraction. We can shortlist important keywords for each section, for example:
```
["experience", "education", "skill", ...]
```
then we split full text by each keyword and find the length from the first string until this word as its value in a dictionary.
```
{"experience": 120, "education": 300, "skill":500, ...}
```
Here we know immediately that "experience section" is between the string index 120 and string index 300. Education section is between string index 300 to 500, and so on.

Refer to the function `detect_sections()` in `information_extraction.py` for an implementation details.

I also apply this to split between multiple experiences in experience section.

........

**Strategy 2 : <br>
Use REGEX whenever possible and avoid large NLP models**

I have experimented with multiple NLP models from huggingface, but most of them are large and slow.

Therefore the first strategy is to do text matching with regex as much as we can.
- REGEX is faster than language model, and more accurate in some cases, but it is rule-based and can overfit.
- Language model can be more generic, and useful, but doesn't guarantee accuracy, and it is resource intensive.

For example, I use `extract_phone_numbers`, in the file `information_extraction.py`, instead of doing a full LM prediction on each word, to find just one number in a resume.
```
def extract_phone_numbers(text):
    """
    return:
        phone_numbers (list): [{"type": "Telephone", "value": "0991234567"}]
    """

    phone_number_pattern = re.compile(r'''
        \b              # Match word boundary
        (?:             # Start of non-capturing group for optional country code
            \+?         # Optional plus sign
            \d{1,2}     # One or two digits for the country code
            \s?         # Optional whitespace character
        )?              # End of non-capturing group, entire group is optional
        \(?             # Optional opening parenthesis
        \d{2,3}         # Two or three digits for the area code
        \)?             # Optional closing parenthesis
        [-.\s]?         # Optional separator character (hyphen, period, space)
        \d{3}           # Three digits
        [-.\s]?         # Optional separator character
        \d{4}           # Four digits
        \b              # Match word boundary
    ''', re.VERBOSE)
    phone_numbers = phone_number_pattern.findall(text)

    phone_numbers_list_of_dict = [{"type": "Telephone", "value": num.replace(" ", "")} for num in phone_numbers]
    
    return phone_numbers_list_of_dict
```

## Extraction of Each Component


### PDF File to Text
Conversion from PDF file to text is handled by the function pdf_to_text that wrap around `pdfminder` library, this function is in the file `text_extraction.py`.

### URL to Text

I simply use Python's requests and read file with `PyPDF2` library. The function `pdf_url_to_text()` will read file and store as plain text. For each request, there will be no file saved, since it's going consume memory.

### Text to Insights
Extracting information from raw text is non-trival task. As there are countless variation of resume structure, choice of word, not to mention the content in the resume it self.

___

*PERSONAL*

- FULL NAME

With text segmentation we are able to get the text in contact section. Which is define as the first string until the start of the next section, which can be anything. The code is generic enough to handle the different section sequence.

Then we use a simple Name Entity Recognition provided by `Spacy` to detect an entity labeled as person.

see `extract_full_name()` function for more details.

- FIRST NAME and FAMILY NAME

I simply use string split to split a full name with white space `" "`. The first part is defined as first name, the later part is defined as family name.

Limitation: Middle name is not covered in this version.

___

*CONTACT* <br>

- EMAIL

I tried a little different technique by using tokenized word, and find a word pattern that matches email structure through the `document.like_email` in Spacy. However, I did not loop over the whole resume. The given text is already selected to be contact section only through the segmentation strategy.

- PHONE

REGEX is appropriate tool and it is able to detect multiple patterns of mobile phone numbers very well. Such as:
```
"+66 90 123 4567", 
"(66) 991234567", 
"0951234567"
...
```
___

*SKILLS* <br>

I have tried a sophisicated Name Entity Recognition package. However, it's time and resouce consuming.

Therefore with a text segmentation strategy in the first step, we are able to retrieve good quality of subset of text related to skill. This will be passed to the function `extract_skills()` that plainly split given text by `","`.

The sophisicated skill extraction is created in a function `extract_skills_comprehensive` that wraps around a Name Entity Recognition package called `SkillNer`. We can specify the threshould as a criteria to select only relevant skills.

For example the model might detect the word "Application" as a skill with confident score 0.5, and detect the word "Machine Learning" with a confident score 0.9. Without the threshold, there would be too many words detected as candidate skills.

___
*EXPERIENCE* <br>

I split experience text section by starting date. Each starting date represents one experience element, i.e. one job. So that we can represent experience data in the following format
```
[
    {"start_date": "...", "company": "...", ..},
    {"start_date": "...", "company": "...", ..},
    ...
]

```

I call each element in the experience list above as `an experience element`.

See `extract_experience()` function, I loop through text and define the first date detected in an experience section as a start date. It is important that we are able to detect end date, since it should be part of the same experience element as the previous start date.

Once we did that, we can identify a string section related to each experience element.

For each string section, we can try to extract information such as company, title, description, and etc. However, with the current model, I can only extract description which is defined by the string section itself.

___
*EDUCATION* <br>

I extracted university name using REGEX pattern. 
```
university_pattern = re.compile(r'''
        \s[^0-9\s]*\sUniversity\s       # <...> University
        |                               # OR
        \sUniversity\sof\s[^0-9\s]*\s   # University of <...>
    ''', re.IGNORECASE | re.DOTALL | re.MULTILINE | re.VERBOSE)
```
The limitation of the code above is that it only detects Univeristy and not the terms Collage or School. More generic pattern needs to be created.

___

The rest of the extraction can be done with either of the 2 strategies as mentioned (1) Regex (2) text classfication, or the following other strategies:

- Question Answering model: put resume as a context, and ask model the question. For example, "what is the most recent company the candidate with working at?"
- Text block segmentation: this can be done either through Computer Vision perspective (density of text) or NLP perspective (text segmentation).
- Custom model using labeled data

## Deployment Strategy
I want to make sure that the model downloading script is done at build time, not during the inference time.

So I created `download_models.py` and run instructed it to run in Dockerfile before running the main file.

```
...

RUN ["python", "download_models.py"]

CMD ["flask", "run", "--host", "0.0.0.0"]
```

All the build and push image scripts are kept in the file `build_and_push_image.bash` where I build a Docker image locally and push it to GCP's Artifact Repository (formerly Cloud Repository)

This cloud-hosted image then can used for a deployment in either GCP Cloud Run or GKE.

Cloud Run is a pay-as-you-go serverless solution, suitable for a small experiment. As the traffic goes higher, switching to a cluster like GKE is a cost-effective decision.

Accepting high through-put like thousands of resume per second requires horizontal node scaling.

While increasing response speed requires improving computation capacity.


## Room for improvement
- Collect resume data and label those data for custom model training
- Work on the rest of the extractable information 
- Unit test
- Better endpoints structure and return codes
- Cleaner, and more optimized coding, or OOP style
- Compute accuracy from sample data

