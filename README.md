# resume-parsing-api

Resume Parsing API receives a pdf as an input and returns an extracted information in JSON format

### Usage
Clone this repository and then run it locally with Docker
```
docker build  -t resume-parsing-image:latest .
docker run -p 5002:5000 resume-parsing-image:latest 
```
Endpoint (can use POSTMAN to test)
```
POST localhost:5002?file_path=<your_file_path>
```
Note that in this version the API does not except real input since it requires either UI to upload file, or a cloud location where users can upload file. `file_path` argument is simply a mockup to demonstrate idea of how file path can be processed further.

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


### Goals
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

### About accuracy
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

### Extraction Strategy
In order to achieve the goal, which is to create API that response within 4 seconds, we need to avoid excessively sophisicated method that yield a little better result but consumes a lot more computational resources.

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


### PDF File to Text
Conversion from PDF file to text is handled by the function pdf_to_text that wrap around `pdfminder` library, this function is in the file `text_extraction.py`.

Input to pdf_to_text function is currently only a single pdf file stored in memory. Ideally, this should be stored externally, for example on-cloud, and we use URL as an input to the API.

### Text to Insights
Extracting information from raw text is non-trival task. As there are countless variation of resume structure, choice of word, not to mention the content in the resume it self.

- SKILLS: 

Skill extraction is done by a function `extract_skills` that wraps around a Name Entity Recognition package called `SkillNer`. We can specify the threshould as a criteria to select only relevant skills.

For example the model might detect the word "Application" as a skill with confident score 0.5, and detect the word "Machine Learning" with a confident score 0.9. Without the threshold, there would be too many words detected as candidate skills.

- CONTACT:

For email, I tried a little different technique by using tokenized word, and find a word pattern that matches email structure through the `document.like_email` in Spacy. However, I did not loop over the whole resume. The variable `n_alphabet` in the function `get_output_dict` is created to limit the number of alphabets go in to the prediction. Here I believe email would likely be in the first 100 words. So I scan the first 100 words for email. In actual work, we might need more data to be decisive about this threshold, or we can use REGEX.

For phone, as mentioned earlier, I tried REGEX and it is able to detect multiple patterns of mobile phone numbers very well. Such as "+66 90 123 4567", "(66) 991234567", or "0951234567". And we only search for the first n words specified by `n_alphabet` as well.

The rest of the extraction can be done with either of the 2 strategies as mentioned (1) Regex (2) text classfication, or the following other strategies:

- Question Answering model: put resume as a context, and ask model the question. For example, "what is the most recent company the candidate with working at?"
- Text block segmentation: this can be done either through Computer Vision perspective (density of text) or NLP perspective (text segmentation). However, these types of strategies require label data.

## Model Storage and Deployment Strategy
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

While increasing response speed requires improving computation capacity per node.


## Room for improvement
- Store resume pdf files on cloud, and use file URL as an input to the resume parsing API.
- Collect resume data and label those data for model training
- Work on the rest of the extractable information 
- Unit test
- Endpoints structure and return codes
- Cleaner, and more optimized coding, or OOP style

