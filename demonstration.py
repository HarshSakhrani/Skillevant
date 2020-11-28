import pandas as pd
import numpy as np
import pickle
import fitz
import re
import statistics 
from statistics import mode 

link="/home/harsh/Downloads/Python Programming An Introduction to Computer Science ( PDFDrive ).pdf"
doc = fitz.open(link) 

from simpletransformers.classification import ClassificationModel
model = ClassificationModel(
    model_type="bert", model_name="/home/harsh/Skillevant_VirtualEnv/Codebase/checkpoint-3696-epoch-3",num_labels=6,use_cuda=False
)

def mostFreqFontsize(page, start, end):
  fontSizes = []
  fontFamilies=[]
  for i in range(start, end):
    index = page[i]

    tempHTMLString = index.getText("html")
    imgOccuranceList = [i.start() for i in re.finditer('<img', tempHTMLString)]
    for i in range(len(imgOccuranceList)):
      tempHTMLString = tempHTMLString.replace(tempHTMLString[tempHTMLString.find('<img'): tempHTMLString.find('>',tempHTMLString.find('<img')) + 1], '<>')
    
    for line in tempHTMLString.splitlines():
      if (line.find('div') == -1 and line.find('<>') == -1):
        individualFont = line[line.find('font-size:') + 10: line.find('pt',line.find('font-size:'))]
        individualFontfamily=line[(line.find("family:"))+7:line.find(";font")]
        individualFontfamily=str(individualFontfamily)
        individualFont = float(individualFont)
        fontSizes.append(individualFont)
        fontFamilies.append(individualFontfamily)

  mostFreqFont = mode(fontSizes)
  mostFreqFontfamily = mode(fontFamilies)
  return mostFreqFont,mostFreqFontfamily


def demonstration(page,start,end):
  dictionary={}
  for i in range(start, end):
    #if i in unwanted:
      #continue
    individualFont = 0
    index = page[i]
    tempHTMLString = index.getText("html")
    imgOccuranceList = [i.start() for i in re.finditer('<img', tempHTMLString)]
    for i in range(len(imgOccuranceList)):
      tempHTMLString = tempHTMLString.replace(tempHTMLString[tempHTMLString.find('<img'): tempHTMLString.find('>',tempHTMLString.find('<img')) + 1], '<>')
    mostFreqFont,mostFreqFontfamily = mostFreqFontsize(page,start,end)
    for line in tempHTMLString.splitlines():
      try:
        if (line.find('div') == -1 and line.find('<>') == -1):
          individualText = line[line.find('>',line.find("<span ")) + 1: line.find('</span>')]
          styling = re.sub(line[line.find('>',line.find("<span ")) + 1: line.find('</span>')],'',line)
          individualFont = line[line.find('font-size:') + 10: line.find('pt',line.find('font-size:'))]
          individualFontfamily=line[(line.find("family:"))+7:line.find(";font")]
          individualFontfamily = str(individualFontfamily)
          individualFont=float(individualFont)

          if ((individualFont != mostFreqFont) or (individualFontfamily != mostFreqFontfamily)): 
            consistentStyling = styling.replace(styling[styling.find(';top'): styling.find('"',styling.find(';left'))], '')
            if  (consistentStyling in list(dictionary.keys())):
              prediction=dictionary[consistentStyling]
            else:
              prediction=model.predict([consistentStyling])
              prediction=prediction[0][0]
            
            if (prediction == 4):
              dictionary[consistentStyling]=prediction
              continue

            if (prediction==0):
              dictionary[consistentStyling]=prediction
              print("Main Heading: ",individualText)
            
            elif (prediction==1):
              dictionary[consistentStyling]=prediction
              temp_heading=individualText
              print("Heading: ",temp_heading)
            
            elif (prediction==2):
              dictionary[consistentStyling]=prediction
              temp_subheading=individualText
              print("Subheading: ",temp_subheading,"   ","Associated Heading:",temp_heading)
            
            elif (prediction==3):
              dictionary[consistentStyling]=prediction
              print("Sub-SubHeading: ",individualText,"    ","Associated Subheading: ",temp_subheading,"   ","Associated Heading:",temp_heading)
            
            elif (prediction==5):
              dictionary[consistentStyling]=prediction
              print("Code: ",individualText)
          
          else:
            print("Content: ",individualText)
      
      except: 
        continue


demonstration(doc,23,28)
