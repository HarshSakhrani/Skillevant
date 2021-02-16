#Necessary Imports
import pandas as pd
import numpy as np
import pickle
import fitz
import re
import statistics 
from statistics import mode 
from py2neo import Graph, Node, Relationship, NodeMatcher
import joblib
from sentence_transformers import SentenceTransformer

#Importing the Model
model = joblib.load("/home/harsh/Skillevant_VirtualEnv/Codebase/Model18.sav")

#Importing PreTrained BERT Sentence Transformer
transformerModel=SentenceTransformer('bert-base-nli-mean-tokens')

graph = Graph("bolt://localhost:7687", auth=("neo4j", "pwd"))  #Kindly Enter your own Auth


def getTempFont(page, start, end):   #Extracting all fonts that exist the pdf
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

    #Extract font-size for each line  
    for line in tempHTMLString.splitlines():
      if (line.find('div') == -1 and line.find('<>') == -1): #To operate on the line, only if div tag and '<>' doesnt exist
        individualFont = line[line.find('font-size:') + 10: line.find('pt',line.find('font-size:'))] #To extract the digits placed such as: 'font-size: 10pt'
        individualFont = float(individualFont) #Convert the str to float
        individualFontfamily=line[(line.find("family:"))+7:line.find(";font")]
        fontFamilies.append(individualFontfamily)
        fontSizes.append(individualFont) #Append to list

  fontSizes = list(set(fontSizes)) #Getting rid of multiple occurences
  fontSizes.sort() #Sorting the list
  return fontSizes


def getMosFreqFont(page, start, end):  #Extacting MostFreqFontSize from the pdf
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

    #Extract font-size for each line  
    for line in tempHTMLString.splitlines():
      if (line.find('div') == -1 and line.find('<>') == -1): #To operate on the line, only if div tag and '<>' doesnt exist
        individualFont = line[line.find('font-size:') + 10: line.find('pt',line.find('font-size:'))] #To extract the digits placed such as: 'font-size: 10pt'
        individualFont = float(individualFont) #Convert the str to float
        individualFontfamily=line[(line.find("family:"))+7:line.find(";font")]
        fontFamilies.append(individualFontfamily)
        fontSizes.append(individualFont) #Append to list

  mostFrequentFont = mode(fontSizes) #Since all the lines are taken into consideration, most frequently occuring font-size is the size of the common text.
  return mostFrequentFont


def removeImg(tempHTMLString):  #Removes HTML Lines which have img tags
  try:
    imgOccuranceList = [i.start() for i in re.finditer('<img', tempHTMLString)]
    for i in range(len(imgOccuranceList)): #Replace all img tags with '<>' 
      tempHTMLString = tempHTMLString.replace(tempHTMLString[tempHTMLString.find('<img'): tempHTMLString.find('>',tempHTMLString.find('<img')) + 1], '<>')  #Converting img tag to "<>"
    tempList=tempHTMLString.splitlines()
    for i in range(len(tempList)):
      if tempList[i]=="<>":
        index=i+1

    tempList.remove(tempList[index])      #Removing lines with "<>"
    tempList.remove(tempList[index-1])    #Removing lines with "<>"
  except:
    pass
  return tempList


def removeChapter(tempHTML,greatestFont):   #Removes Extra Chapter Information like "Chapter:1"
  #tempHTML=tempHTMLString.splitlines()
  try:
    for i in range(len(tempHTML)):
      if (tempHTML[i].find('div') == -1 and tempHTML[i].find('<>') == -1):
        individualFont = tempHTML[i][tempHTML[i].find('font-size:') + 10: tempHTML[i].find('pt',tempHTML[i].find('font-size:'))] #To extract the digits placed such as: 'font-size: 10pt'
        individualFont = float(individualFont)
        if(individualFont==greatestFont):   #HTML line with the highest font size is located. aka Chapter Heading
          index=i
          break
    tempHTML.remove(tempHTML[index-1])  #The line before the Chapter Heading Line is removed.

  except:
    pass

  return tempHTML


def getGreatestFont(page,start,end,numberOfChapters):
  dictionary={}   #Map to keep a track of occurances and freq
  for i in getTempFont(page,start,end):
    dictionary[i]=0
  for i in range(start,end):
    try:
      index = page[i]

      #getText("html"): used to extract the html of that particular page
      tempHTMLString = index.getText("html")

      #Used to find the location of img tags: for 5 occurences, imgOccuraanceList holds five positions
      imgOccuranceList = [i.start() for i in re.finditer('<img', tempHTMLString)]
      for i in range(len(imgOccuranceList)): #Replace all img tags with '<>' 
        tempHTMLString = tempHTMLString.replace(tempHTMLString[tempHTMLString.find('<img'): tempHTMLString.find('>',tempHTMLString.find('<img')) + 1], '<>')

      #Extract font-size for each line  
      for line in tempHTMLString.splitlines():
        if (line.find('div') == -1 and line.find('<>') == -1): #To operate on the line, only if div tag and '<>' doesnt exist
          individualFont = line[line.find('font-size:') + 10: line.find('pt',line.find('font-size:'))] #To extract the digits placed such as: 'font-size: 10pt'
          individualFont = float(individualFont) #Convert the str to float
          #if individualFont==16:
            #print(line)
          dictionary[individualFont]+=1
    except:
      continue

  #return dictionary
  for key,value in sorted(list(dictionary.items()), reverse=True):  #Sorted in the descending order to probabilistically get the Chapter Heading depending on the frequency
    if value>numberOfChapters-1:    #The condition makes sure that you get the Chapter heading on the basis of freq and not some garbage higher fonts that might be one offs
      greatestFont=key
      break
  
  return greatestFont


def getAllFonts(page,start,end,numberOfChapters):   #Extracts fonts corresponding to Chapter Heading, Main Heading and SubHeading
  fontList=[]
  dictionary={}   #Map to keep a track of occurances and freq
  for i in getTempFont(page,start,end):
    dictionary[i]=0

  highestFont=getGreatestFont(page,start,end,numberOfChapters)
  mostFreqFont=getMosFreqFont(page,start,end)
  for i in range(start,end):
    try:
      index=page[i]

      tempHTMLString = index.getText("html")
      tempHTMLList=removeImg(tempHTMLString)
      tempHTMLList=removeChapter(tempHTMLList,highestFont)

      for line in tempHTMLList:
        if (line.find('div') == -1 and line.find('<>') == -1):
          individualFont = line[line.find('font-size:') + 10: line.find('pt',line.find('font-size:'))]
          individualFont = float(individualFont)      
          dictionary[individualFont]+=1
    except:
      continue
    
  keys=list(dictionary.keys())
  keys=[key for key in keys if key > mostFreqFont]  #Chapter Heading, Main Heading and SubHeading generally have a fontsize greater than the mostfreqfont. This condition makes sure that further computation is done only on those fonts
  tempDict = {key:dictionary[key] for key in keys}

  if (len(tempDict)==1):
    for key,value in sorted(list(tempDict.items()), reverse=True):
      fontList.append(key)
      
  else:
    for key,value in sorted(list(tempDict.items()), reverse=True):
      if (len(fontList)==2):    #Finding out fontsizes corresponding to Main Heading and SubHeading
        break
      if ((key<highestFont) and (value > (tempDict[highestFont]+10))):  #Both these font sizes have to be less than the highest font and their freq should be much higher than the freq of the highest font
        fontList.append(key)
  
  fontList.append(highestFont)  #FontSize corresponding to the Chapter Heading
  fontList.sort()   
  return fontList

def find_max_mode(list1):  #Sophisticated Technique to find out mode. Makes sure to give the result even if there is a tie
    list_table = statistics._counts(list1)
    len_table = len(list_table)

    if len_table == 1:
        max_mode = statistics.mode(list1)
    else:
        new_list = []
        for i in range(len_table):
            new_list.append(list_table[i][0])
        max_mode = max(new_list) # use the max value here
    return max_mode


def mostFreqFontsize(page, start, end): #Extracts MostFreqFontSize and MostFreqFontFamily
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

  mostFreqFont = find_max_mode(fontSizes)   #Since all the lines are taken into consideration, most frequently occuring font-size is the size of the common text.
  mostFreqFontfamily = find_max_mode(fontFamilies)    #Since all the lines are taken into consideration, most frequently occuring font-family is the font-family of the common text.
  return mostFreqFont,mostFreqFontfamily


def extraStringLength(tempHTMLString):    #Splits the html string into multiple strings if the string is a combination of more than one strings
  tempList=[]
  startList=[k.start() for k in re.finditer('<span ', tempHTMLString)] #List with start points of all html strings 
  endList=[k.start() for k in re.finditer('</span>', tempHTMLString)]   #List with end points of all html strings
  constStart=tempHTMLString[:tempHTMLString.find("""pt">""")+4]   #Extracting constant part of each string 
  for k in range(len(startList)):
    tempString=constStart+tempHTMLString[startList[k]:endList[k]+7]   #One of the many strings 
    tempList.append(tempString) 
  return tempList


def getContentFontsizeFontfamily(page,startBook,startChap,end,numberOfChapters):  #Extracting FontSize and FontFamily corresponding to Core Content
  highestFont=getGreatestFont(page,startBook,end,numberOfChapters)  #Greatest Font
  tempList=getAllFonts(page,startBook,end,numberOfChapters) #Fonts corresponding to Chapter Heading, Main Heading and SubHeading
  maxVal=0
  contentCount=0
  codeCount=0
  dictionary={("y",0):(0,0)}  #Keys:FontFamily, FontSize    #Values:Freq of Content, Freq of Code
  tempDict={("x",0):(0,0)}    #Keys:FontFamily, FontSize    #Values: Overall Freq, 0/1 => Content/Code
  i=startChap-1
  while(1):
    i+=1      
    individualFont = 0
    index = page[i]
    
    tempHTMLString = index.getText("html")
    tempHTMLList=removeImg(tempHTMLString)
    tempHTMLList=removeChapter(tempHTMLList,highestFont)
    
    for tempLine in tempHTMLList:
      try:
        for line in extraStringLength(tempHTMLString=tempLine):
          if (line.find('div') == -1 and line.find('<>') == -1):
            individualText = line[line.find('>',line.find("<span ")) + 1: line.find('</span>')]
            styling = re.sub(line[line.find('>',line.find("<span ")) + 1: line.find('</span>')],'',line)
            individualFont = line[line.find('font-size:') + 10: line.find('pt',line.find('font-size:'))]
            individualFontfamily=line[(line.find("family:"))+7:line.find(";font")]
            individualFontfamily = str(individualFontfamily)
            individualFont=float(individualFont)
            if individualText==" ":
              continue

            if (individualFont==tempList[len(tempList)-1]):
              pass

            elif (individualFont==tempList[len(tempList)-2]):
              pass
            
            elif (individualFont==tempList[len(tempList)-3]):             
              pass

            else:
              individualTextVec=transformerModel.encode([individualText])[0]  #Encoding the html string text using Sentence Transformer
              individualTextVec=individualTextVec.reshape(1,-1)   
              prediction=model.predict(individualTextVec)   #RandomForest Prediction
              prediction=prediction[0]

              if (individualFontfamily,individualFont) not in dictionary:
                dictionary[(individualFontfamily,individualFont)]=[0,0] #Initializing respective key values

              if prediction==0: #Label corresponding to Content
                contentCount+=1
                dictionary[(individualFontfamily,individualFont)][0]+=1   #Increasing the Content freq of the corresponding FontFamily and FontSize
                continue
              
              else:   #Label corresponding to Code
                codeCount+=1  
                dictionary[individualFontfamily,individualFont][1]+=1   #Increasing the Code freq of the corresponding FontFamily and FontSize
      except: 
        continue
    if (contentCount>40):   #Breaking after observing a sufficient number of examples
      break

  for keys in dictionary.keys():    #Initializing tempDict(Keys:FontFamily, FontSize    #Values: Overall Freq, 0/1 => Content/Code)
    tempDict[keys]=[0,0]
    tempDict[keys][0]=dictionary[keys][0]+dictionary[keys][1]
    if dictionary[keys][0]>dictionary[keys][1]:
      tempDict[keys][1]=0
    else:
      tempDict[keys][1]=1
    
  for keys in tempDict.keys():  #Extracting contentFontFamily and contentFontSize for every chapter
    if ((tempDict[keys][0]>maxVal) and (tempDict[keys][1]==0)):   #Finding out the key with the higest Overall Freq and Content Label
      maxVal=tempDict[keys][0]
      contentFontFamily,contentFontSize=keys 
  return contentFontFamily,contentFontSize

def createDB(dictionary,bookName):
  temp2NodeType=""    
  bookTitleNode = Node("MainTitle", name=bookName)  #Creating central node
  graph.create(bookTitleNode)
  for keys,values in dictionary.items():
    if keys[3]=="":
      continue
    temp1=Node(keys[3],name=keys[1]) #Creating a node with a given relation and name 
    temp1['Content']=values[0]
    temp1['Code']=values[1]
    if keys[3]=="MainHeading":  #Finding out the node type of the other half of the relation
      temp2NodeType="MainTitle"
    elif keys[3]=="Heading":  #Finding out the node type of the  other half of the relation
      temp2NodeType="MainHeading"
    elif keys[3]=="SubHeading": #Finding out the node type of the  other half of the relation
      temp2NodeType="Heading"
    elif keys[3]=="SubSubHeading":  #Finding out the node type of the  other half of the relation
      temp2NodeType="SubHeading"
    matcher=NodeMatcher(graph)
    temp2=matcher.match(temp2NodeType,name=str(keys[0])).first()  #Finding out the other half of the relation in the grpah
    temp_var=Relationship.type(keys[2])
    relation=temp_var(temp1,temp2)  
    graph.create(relation) #Creating a relationship between the two

def demonstration(page,start,end,bookName,numberOfChapters):
  highestFont=getGreatestFont(page,start,end,numberOfChapters)    #Extracting Greatest Font
  tempList=getAllFonts(page,start,end,numberOfChapters)   #Fonts corresponding to Chapter Heading, Main Heading and SubHeading
  pageFlag=0
  headingCount=0
  pageCount=0
  temp1=""
  temp2=""
  db_temp_dictionary={("","","",""):["",""]}    #Keys: 1. String with which Relation has to be formed   Values: ContextText, CodeText
                                                #      2. Current String
                                                #      3. Relation 
                                                #      4. Type of Node (Chapter Heading, Main Heading, Sub Heading)

  for i in range(start,end):
    print(i)
    pageCount+=1
    presenceOfContent=0      
    individualFont = 0
    index = page[i]
    

    tempHTMLString = index.getText("html")
    tempHTMLList=removeImg(tempHTMLString)    #Removes Img Tags
    tempHTMLList=removeChapter(tempHTMLList,highestFont)  #Removes Extra Chapter Info (Eg: Chapter 1)
    

    for tempLine in tempHTMLList:
      try:
        for line in extraStringLength(tempHTMLString=tempLine):
          if (line.find('div') == -1 and line.find('<>') == -1):
            individualText = line[line.find('>',line.find("<span ")) + 1: line.find('</span>')]
            styling = re.sub(line[line.find('>',line.find("<span ")) + 1: line.find('</span>')],'',line)
            individualFont = line[line.find('font-size:') + 10: line.find('pt',line.find('font-size:'))]
            individualFontfamily=line[(line.find("family:"))+7:line.find(";font")]
            individualFontfamily = str(individualFontfamily)
            individualFont=float(individualFont)
            if individualText==" ":
              continue

            if (individualFont==tempList[len(tempList)-1]):
              if pageFlag==0:
                #if (headingCount==(len(headingList)-1)):
                  #mostFreqFont,mostFreqFontfamily = mostFreqFontsize(page,headingList[headingCount],end)
                #else:
                  #mostFreqFont,mostFreqFontfamily = mostFreqFontsize(page,headingList[headingCount],headingList[headingCount+1])
                mostFreqFontfamily,mostFreqFont=getContentFontsizeFontfamily(page,start,i,end,numberOfChapters)
                #print(mostFreqFont,",",mostFreqFontfamily)
                count=0
                temp_mainheading=individualText #Keeping a track of Previous MainHeading
                temp1=bookName    #(String with which Relation has to be formed) BookName
                temp2=individualText  #Current Individual Text
                temp_relation="Chapter" #Relation
                temp_type="MainHeading" #Type of Node (Chapter Heading, Main Heading, Sub Heading)
                print("Main Heading: ",individualText)    
                headingCount+=1
                presenceOfContent=0
                pageFlag=1
              else:
                continue
            
            elif (individualFont==tempList[len(tempList)-2]):
              if presenceOfContent==0:
                db_temp_dictionary[(temp1,temp2,temp_relation,temp_type)]=["",""]
              count=0
              temp_heading=individualText #Keeping a track of Previous Heading
              if presenceOfContent==1:
                temp1=temp_mainheading  #(String with which Relation has to be formed) MainHeading
                temp2=individualText  
                temp_relation="Heading"
                temp_type="Heading"
              else:
                temp1=temp_mainheading 
                temp2=individualText
                temp_relation="Heading"
                temp_type="Heading"                
              print("Heading: ",temp_heading)
              presenceOfContent=0
              pageFlag=0
            
            elif (individualFont==tempList[len(tempList)-3]):
              if presenceOfContent==0:
                db_temp_dictionary[(temp1,temp2,temp_relation,temp_type)]=["",""]
              count=0              
              temp_subheading=individualText  #Keeping a track of Previous SubHeading
              if presenceOfContent==1:
                temp1=temp_heading  #(String with which Relation has to be formed) Heading
                temp2=individualText
                temp_relation="SubHeading"
                temp_type="SubHeading"
              else:
                temp1=temp_heading
                temp2=individualText
                temp_relation="SubHeading"
                temp_type="SubHeading"
              print("Subheading: ",temp_subheading,"   ","Associated Heading:",temp_heading)
              presenceOfContent=0      
              pageFlag=0        
            
            else:
              pageFlag=0
              presenceOfContent=1

              if (temp1,temp2,temp_relation,temp_type) not in db_temp_dictionary.keys():
                db_temp_dictionary[(temp1,temp2,temp_relation,temp_type)]=["",""] #Initializing Dictionary

              if ((individualFontfamily==mostFreqFontfamily) and (individualFont==mostFreqFont)): #Comparing with ContentFontSize and ContentFontFamily
                print("Content: ",individualText) 
                db_temp_dictionary[(temp1,temp2,temp_relation,temp_type)][0]=db_temp_dictionary[(temp1,temp2,temp_relation,temp_type)][0]+'\n'+individualText #Adding content to value of corresponding fontsize and fontfamily
                continue
              
              else:
                print("Code: ",individualText)
                db_temp_dictionary[(temp1,temp2,temp_relation,temp_type)][1]=db_temp_dictionary[(temp1,temp2,temp_relation,temp_type)][1]+'\n'+individualText #Adding code to value of corresponding fontsize and fontfamily
      except: 
        continue
  createDB(db_temp_dictionary,bookName)

if __name__ == '__main__':
    link="/home/harsh/Downloads/PDFs-20201229T074819Z-001/PDFs/Graph_Databases_2e_Neo4j.pdf"
    doc = fitz.open(link)
    demonstration(doc,18,210,"Graph",7) 
