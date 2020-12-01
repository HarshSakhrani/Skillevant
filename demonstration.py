#Import essential libraries
import pandas as pd
import numpy as np
import pickle
import fitz
import re
import statistics 
from statistics import mode
from simpletransformers.classification import ClassificationModel 

#Pathname to PDF
link="/home/harsh/Downloads/Python Programming An Introduction to Computer Science ( PDFDrive ).pdf"

#Open PDF
doc = fitz.open(link) 

#Load a classification model - make sure to add the correct file path to the model (No GPU Required)
model = ClassificationModel(
    model_type="bert", model_name="/home/harsh/Skillevant_VirtualEnv/Codebase/checkpoint-3696-epoch-3",num_labels=6,use_cuda=False
)


def mostFreqFontsize(page, start, end):
  fontSizes = []
  fontFamilies=[]
  for i in range(start, end):
    index = page[i]

    #getText("html"): used to extract the html of that particular page
    tempHTMLString = index.getText("html")

    #Used to find the location of img tags: for 5 occurences, imgOccuraanceList holds five positions
    imgOccuranceList = [i.start() for i in re.finditer('<img', tempHTMLString)]
    for i in range(len(imgOccuranceList)): #Replace all img tags with '<>' 
      tempHTMLString = tempHTMLString.replace(tempHTMLString[tempHTMLString.find('<img'): tempHTMLString.find('>',tempHTMLString.find('<img')) + 1], '<>')
    
    for line in tempHTMLString.splitlines():
      if (line.find('div') == -1 and line.find('<>') == -1): #To operate on the line, only if div tag and '<>' doesnt exist
        individualFont = line[line.find('font-size:') + 10: line.find('pt',line.find('font-size:'))] #To extract the digits placed such as: 'font-size: 10pt'
        individualFontfamily=line[(line.find("family:"))+7:line.find(";font")] #To extract font family 
        individualFontfamily=str(individualFontfamily) #Convert to str
        individualFont = float(individualFont) #Convert to float
        fontSizes.append(individualFont) #Append to list
        fontFamilies.append(individualFontfamily) #Append to list

  mostFreqFont = mode(fontSizes) #Since all the lines are taken into consideration, most frequently occuring font-size is the size of the common text.
  mostFreqFontfamily = mode(fontFamilies) #Since all the lines are taken into consideration, most frequently occuring font-family is the one of the common text.
  return mostFreqFont,mostFreqFontfamily


def demonstration(page,start,end):
  dictionary={}
  for i in range(start, end):
    
    individualFont = 0
    index = page[i]

    #getText("html"): used to extract the html of that particular page
    tempHTMLString = index.getText("html")

    #Used to find the location of img tags: for 5 occurences, imgOccuraanceList holds five positions
    imgOccuranceList = [i.start() for i in re.finditer('<img', tempHTMLString)]
    for i in range(len(imgOccuranceList)):
      tempHTMLString = tempHTMLString.replace(tempHTMLString[tempHTMLString.find('<img'): tempHTMLString.find('>',tempHTMLString.find('<img')) + 1], '<>')

    #Retrieve font-size and font-family of normal text
    mostFreqFont,mostFreqFontfamily = mostFreqFontsize(page,start,end)

    for line in tempHTMLString.splitlines():
      try:
        if (line.find('div') == -1 and line.find('<>') == -1): #To operate on the line, only if div tag and '<>' doesnt exist
          individualText = line[line.find('>',line.find("<span ")) + 1: line.find('</span>')] #To extract text placed in between span tags
          styling = re.sub(line[line.find('>',line.find("<span ")) + 1: line.find('</span>')],'',line) #To replace text placed in between span tags
          individualFont = line[line.find('font-size:') + 10: line.find('pt',line.find('font-size:'))] #To extract the digits placed such as: 'font-size: 10pt'
          individualFontfamily=line[(line.find("family:"))+7:line.find(";font")] #To extract the font family 
          individualFontfamily = str(individualFontfamily) #Convert to str
          individualFont=float(individualFont) #Convert to float

          if ((individualFont != mostFreqFont) or (individualFontfamily != mostFreqFontfamily)): #To continue only if styling is not of normal text: 
            consistentStyling = styling.replace(styling[styling.find(';top'): styling.find('"',styling.find(';left'))], '') #Get rid of unnecessary styling elements such as top, left

            if  (consistentStyling in list(dictionary.keys())): #Styling is present in list
              prediction=dictionary[consistentStyling] #Prediction now holds label for that styling
            else: #Styling is not present in list
              prediction=model.predict([consistentStyling]) #Predict label for styling using model loaded above
              prediction=prediction[0][0]
            
            if (prediction == 4): #Header/Footer
              dictionary[consistentStyling]=prediction #For this styling: label 4
              continue #Ignore 

            if (prediction==0): #Main Heading
              dictionary[consistentStyling]=prediction #For this styling: label 0
              print("Main Heading: ",individualText)
            
            elif (prediction==1): #Heading
              dictionary[consistentStyling]=prediction #For this styling: label 1
              temp_heading=individualText
              print("Heading: ",temp_heading)
            
            elif (prediction==2): #Sub heading
              dictionary[consistentStyling]=prediction #For this styling: label 2
              temp_subheading=individualText
              print("Subheading: ",temp_subheading,"   ","Associated Heading:",temp_heading)
            
            elif (prediction==3): #Sub sub heading
              dictionary[consistentStyling]=prediction #For this styling: label 3
              print("Sub-SubHeading: ",individualText,"    ","Associated Subheading: ",temp_subheading,"   ","Associated Heading:",temp_heading)
            
            elif (prediction==5): #Code
              dictionary[consistentStyling]=prediction #For this styling: label 5
              print("Code: ",individualText)
          
          else:
            print("Content: ",individualText) #Normal text: most frequent text, most frequent font-family
      
      except: 
        continue


demonstration(doc,23,28)
