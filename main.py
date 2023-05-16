
from typing import Optional

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
import requests

app = FastAPI()


class Contact(BaseModel):
    # name: str
    firstName: str
    lastName: str
    companyName: Optional[str] = None
    domain: Optional[str] = None
    # email: Optional[str] = None
    # emailValid: Optional[bool] = None


    def patternCollection(self, urlEmail, patternCounter, otherEmails):

        firstNameCompany = self.firstName+"@"+self.domain
        lastNameCompany = self.lastName+ "@" + self.domain
        firstNameDOTlastNameCompany = self.firstName+"."+self.lastName+ "@" + self.domain
        firstLetterFirstNameLastNameCompany = self.firstName[0]+self.lastName+"@"+ self.domain
        #patternCounterSave = self.patternCounter

        #making sure that email domain is not empty and also that there is an email to compare with
        if (self.domain != "") and (urlEmail != ""):

            if (firstNameCompany.lower() == urlEmail.lower()):
                patternCounter['firstNameCompany'] += 1
            elif (lastNameCompany.lower() == urlEmail.lower()):
                patternCounter['lastNameCompany'] += 1
            elif (firstNameDOTlastNameCompany.lower() == urlEmail.lower()):
                patternCounter['firstNameDOTlastNameCompany'] += 1
            elif (firstLetterFirstNameLastNameCompany.lower() == urlEmail.lower()):
                patternCounter['firstLetterFirstNameLastNameCompany'] += 1
            else:
                patternCounter['otherEmails'] += 1
                otherEmails.append({'email': urlEmail.lower(), 'firstName': self.firstName, 'lastName': self.lastName})
                #print("the outlier pattern is: " + urlEmail + " , for contact " + self.firstName + " " + self.lastName + " who works at " + self.companyName)
                #patternCounter['outlierPattern'] += 1
        return [patternCounter, otherEmails]




def findCompanyEmail(firstName, lastName, domain, patternCounter):

    possibleEmails = []
    otherEmails = []
    #print(list(patternCounter.values()))
    for key, value in patternCounter.items():
        # Dont want to count the pattern with no value
        if value > 1:
            email=''
            # newPatternDict[key] = value
            if key == 'firstNameDOTlastNameCompany':
                email = firstName.lower() + "." + lastName.lower() + "@" + domain
            elif key == 'firstLetterFirstNameLastNameCompany':
                email = firstName[0].lower() + lastName.lower() + "@" + domain
            elif key == 'firstNameCompany':
                email = firstName.lower() + "@" + domain
            elif key == 'lastNameCompany':
                email = lastName.lower() + "@" + domain
            possibleEmails.append({'pattern': key, 'email': email,'weight': value})
        else:
            pass

    return possibleEmails


@app.get("/")
def init():
    return {'status': 'sucess'}

@app.post("/")
def find_email(contact: Contact):
    domain = contact.domain
    firstName = contact.firstName
    lastName = contact.lastName

    # Find all contact we already know
    response = requests.get("https://sales-machine.vizir.co/contacts?website="+domain)
    contactList = response.json()

    if ('www.' in domain):
        domain = domain[4: len(domain)]
        response2 = requests.get("https://sales-machine.vizir.co/contacts?website="+domain)
        contactList2 = response2.json()
        if len(contactList2) > 1:
            for cont in contactList2:
                contactList.append(cont)
    else:
        domain2 = 'www.' + domain
        response2 = requests.get("https://sales-machine.vizir.co/contacts?website="+domain2)
        contactList2 = response2.json()
        if len(contactList2) > 1:
            for cont in contactList2:
                contactList.append(cont)


    # ContactList has all the contact of the company

    patternCounter = {}
    # @TODO we need to make sure we have all the patterns
    # Note: the best way to do it is to creaate a function in order to find the the pattern present in the sales machine
    # If no pattern is present we wont try to find the email in the first version
    patternCounter['firstNameCompany'] = 0
    patternCounter['lastNameCompany'] = 0
    patternCounter['firstNameDOTlastNameCompany'] = 0
    patternCounter['firstLetterFirstNameLastNameCompany'] = 0
    patternCounter['outlierPattern'] = 0
    patternCounter['otherEmails'] = 0
    patternCounter['noEmail'] = 0
    otherEmails = []



    # DATA: @TODO
    # From contactList we need to find the pattern for theses specific cases
    # - apostrophe in the first name and or the lastName (guivarc'h)
    # - prénom composé (Jean-Marc, jean marc, ...)
    # - Nom composé (Le Maire, Le duff, ...)

    # The best way to do it is to create a company Model.
    # with emailsPatterns, apostrophePattern, firstNamePattern, lastNamePattern, ...
    # Then for each pattern we create a function in order to get the good value.

    for x in contactList:
        #this takes the email stored in the url and temporarily saves as a string in emailSaved
        if 'email' in x:
            urlEmailSaved = x['email']
            #makes sure that the email is completely lower case
            urlEmailSaved = urlEmailSaved.lower()

            #separates the urlEmail into "before @", "@", and "after @""
            emailPieces = urlEmailSaved.partition("@")

            #this is the domain part, this is "after @""
            domainPieceUrl = emailPieces[2]

            #this takes the name (usually has both first and last names) stored in the url and temporarily saves as a string in nameSaved
            companyNameUrl = x['companyName']
            nameSaved = x['name']
            #making sure that nameSaved is not empty
            if nameSaved != "":

                #separating nameSaved into the first and last name for later pattern recognition
                separateNameUrl = nameSaved.split()

                # firstNameUrl = ""
                # lastNameUrl = ""
                # if firstName in x:
                #     firstNameUrl = x.firstName
                # if lastName in x:
                #     lastNameUrl = x.lastName

                # if firstNameUrl != "":
                #     firstNameUrl = nameSaved.difference(lastNameUrl)

                if len(separateNameUrl) > 1:
                    firstNameUrl = separateNameUrl[0]
                    lastNameUrl = separateNameUrl[1]

                    contactData  = {
                        'firstName': firstNameUrl,
                        'lastName': lastNameUrl,
                        'companyName': companyNameUrl,
                        'domain': domainPieceUrl
                    }
                    #creating a new email with the Url information -- this is going to be the email that is passed into pattern recognition
                    email = Contact(**contactData)


                    [patternCounter, otherEmails] = email.patternCollection(urlEmailSaved, patternCounter, otherEmails)

        patternCounter['noEmail'] += 1
    data = findCompanyEmail(firstName, lastName, domain, patternCounter)
    return {'status': 'success', 'email_finder': data, 'other_emails': otherEmails}
