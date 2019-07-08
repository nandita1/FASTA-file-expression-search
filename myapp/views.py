from django.shortcuts import render
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError
import requests
import re
from dna_features_viewer import GraphicFeature, GraphicRecord
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
# Create your views here.

#function to replace image name unwanted characters by _
def replaceMultiple(mainString, toBeReplaces, newString):
    # Iterate over the strings to be replaced
    for elem in toBeReplaces :
        # Check if string is in the main string
        if elem in mainString :
            # Replace the string
            mainString = mainString.replace(elem, newString)

    return  mainString

'''
When we upload a fasta file with multiple sequences
>gi|545778205|gb|U00096.3|:190-255 Escherichia coli str. K-12 substr. MG1655, complete genome
ATGAAACGCATTAGCACCACCATTACCACCACCATCACCATTACCACAGGTAACGGTGCGGGCTGA
>gi|545778205|gb|U00096.3|:337-2799 Escherichia coli str. K-12 substr. MG1655, complete genome
ATGCGAGTGTTGAAGTTCGGCGGTACATCAGTGGCAAATGCAGAACGTTTTCTGCGTGTTGCCGATATTC
'''
#For Multiple Sequence Files
def upload(request):
    info=[]
    gene_sequence=[]
    titles=[]
    all_locations=[]
    i=-1
    zipped = {}
    uploaded_file = ''
    expression = ''
    figure_names=[]
    posted = False
    length = 0
    no_of_matches = 0
    matched_sequences = []
    matched_strings = []
    if request.method == 'POST':
        posted = True
        #get the uploaded file
        uploaded_file = request.FILES['document']
        #for every line in the file
        for line in uploaded_file:
            #convert from binary format to ascii format
            line = line.decode('utf-8')
            #get the title in info
            if line[0] == '>':
                line = line.rstrip('\n')
                info.append(line.strip('>'))
                i = i + 1
                gene_sequence.append("")
            #else get the gene sequences
            else:
                gene_sequence[i]+=line.strip()
        j=i
        length = i+1
        #if user inputs a string
        if request.POST.get('expression'):
            expression = request.POST.get('expression')

            #for every gene sequence
            for i in range(j):
                list_expression = []
                list_expression.append(expression)
                features=[]
                #if the string is present in the sequence
                if(gene_sequence[i].find(expression))!=-1:
                    matched_sequences.append(gene_sequence[i])
                    matched_strings.append(list_expression)
                    #get the locations where it is present
                    locations = [m.start() for m in re.finditer(expression, gene_sequence[i])]
                    #titles will hold all the titles of the matched sequences
                    titles.append(info[i])
                    #all the locations
                    all_locations.append(locations)
                    for location in locations:
                        features.append(GraphicFeature(start=location+0.5, end=location+len(expression)+0.5, strand=+1, color="#ffd700",label=expression))
                    record = GraphicRecord(sequence_length=len(gene_sequence[i]), features=features)
                    #record = record.crop((locations[0],locations[-1]+len(expression)+1))
                    ax, _ = record.plot(figure_width=30)
                    #print(info[i].split())
                    new_info = replaceMultiple(info[i].split()[0], ['|',':'] , '_')
                    figure_names.append('sequence_and_translation'+new_info+expression+'.png')
                    #print(figure_names)
                    ax.figure.savefig('myapp/static/sequence_and_translation'+new_info+expression+'.png', bbox_inches='tight')
        #else if the user inputs a regular expression
        elif request.POST.get('regex'):
            expression = request.POST.get('regex')
            #compile the regular expression for further processing
            expression = re.compile(expression)
            #for every sequence
            for i in range(i):
                features = []
                #findall returns the matched parts in the sequence
                #if the whole expression is put in bracket it returns the matched part as well as the part further in the bracket in a tuple
                matches = re.findall(expression, gene_sequence[i])
                #take the unique sequences
                matches = set(matches)
                matches = list(matches)

                locations = []
                exact_matches=[]
                #if there are matches
                if matches!=[]:
                    if type(matches[0]) is tuple:
                        #since the exact match is the 1st element of every tuple in the matches list
                        for match in matches:
                            exact_matches.append(match[0])
                    else:
                        exact_matches = matches
                    print(exact_matches)
                    matched_sequences.append(gene_sequence[i])
                    matched_strings.append(exact_matches)
                    #for every matched string we find its location
                    for match in exact_matches:
                        locations+=[m.start() for m in re.finditer(match, gene_sequence[i])]
                        graph_locations = [m.start() for m in re.finditer(match, gene_sequence[i])]
                        for graph_location in graph_locations:
                            features.append(GraphicFeature(start=graph_location+0.5, end=graph_location+len(match)+0.5, strand=+1, color="#ffd700",label=match))
                    record = GraphicRecord(sequence_length=len(gene_sequence[i]), features=features)
                    #record = record.crop((locations[0],locations[-1]+len(expression)+1))
                    ax, _ = record.plot(figure_width=30)
                    #print(info[i].split())
                    new_info = replaceMultiple(info[i].split()[0], ['|',':'] , '_')
                    figure_names.append('sequence_and_translation'+new_info+str(expression)+'.png')
                    #print(figure_names)
                    ax.figure.savefig('myapp/static/sequence_and_translation'+new_info+str(expression)+'.png', bbox_inches='tight')
                    #append the title of the gene sequence where there is a match
                    titles.append(info[i])
                    all_locations.append(locations)
        #zip the two lists to iterate over it in the html document simultaneously
        print(matched_strings)
        no_of_matches = len(titles)
        list_of_ids = list(range(no_of_matches))
        zipped = tuple(zip(titles, all_locations,figure_names, matched_sequences, matched_strings, list_of_ids))
    return render(request, 'upload.html',{'zipped': zipped,'posted':posted, 'length': length, 'no_of_matches': no_of_matches})




'''
When we get the fasta format from NCBI by providing the protein_id
>sp|P48740.3|MASP1_HUMAN RecName: Full=Mannan-binding lectin serine protease 1; AltName: Full=Complement factor MASP-3; AltName: Full=Complement-activating component of Ra-reactive factor; AltName: Full=Mannose-binding lectin-associated serine protease 1; Short=MASP-1; AltName: Full=Mannose-binding protein-associated serine protease; AltName: Full=Ra-reactive factor serine protease p100; Short=RaRF; AltName: Full=Serine protease 5; Contains: RecName: Full=Mannan-binding lectin serine protease 1 heavy chain; Contains: RecName: Full=Mannan-binding lectin serine protease 1 light chain; Flags: Precursor
MRWLLLYYALCFSLSKASAHTVELNNMFGQIQSPGYPDSYPSDSEVTWNITVPDGFRIKLYFMHFNLESS

Since the content is dynamically loaded and not available in text format directly we have to do web scraping
1. Go to network console of https://www.ncbi.nlm.nih.gov/protein/P48740/?report=fasta
2. Get the url of viewer.fcgi
3. Find the id present in the url in the page source of the website
4. The id is the value attribute of the div element with id as viewercontent1
5. Use BeautifulSoup to get the content/text inside this element which is our fasta_file as text
'''
#For ncbi
def ncbi(request):
    info=''
    gene_sequence=''
    title=''
    locations=[]
    expression = ''
    features = []
    protein_id=''
    nucleo_id = ''
    figure_name = ''
    connection = True
    posted = False
    if request.method == 'POST':
        posted = True
        if request.POST.get("protein_id"):
            #get the protein_id and add it to the url to fetch the fasta file
            protein_id = request.POST.get("protein_id")
            url = "https://www.ncbi.nlm.nih.gov/protein/"+protein_id+"/?report=fasta"
            try:
                file = requests.get(url)
            except ConnectionError:
                print ('Failed to open url.')
                connection = False
            else:
                #since an HTML file is returned convert it into string format
                html_file = file.content
                html_file = html_file.decode('utf-8')

                #to get the text file we need the id present in the value attribute of div element with id viewercontent1
                #BeautifulSoup is used for web scraping
                soup = BeautifulSoup(html_file, 'html.parser')
                mydiv = soup.find(id = "viewercontent1")

                #the url which consists the fasta file in text format
                fasta_url ="https://www.ncbi.nlm.nih.gov/sviewer/viewer.fcgi?id="+str(mydiv.get('val'))+"&db=protein&report=fasta&retmode=text&withmarkup=on&tool=portal&log$=seqview&maxdownloadsize=1000000"
                file = requests.get(fasta_url)
                fasta_file = file.content
                fasta_file = fasta_file.decode('utf-8')
        elif request.POST.get("nucleo_id"):
            nucleo_id = request.POST.get("nucleo_id")
            driver = webdriver.Chrome(executable_path="C:\\Users\\Hp\\Documents\\chromedriver.exe")
            try:
                driver.get("https://www.ncbi.nlm.nih.gov/nuccore/"+nucleo_id+"?report=fasta&log$=seqview&format=text")
            except ConnectionError:
                print('Failed to open URL')
                connection = False
            else:
                try:
                    element = WebDriverWait(driver, 1000000).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "fixedboxComplete"))
                        )
                finally:
                    element = driver.find_element_by_id("viewercontent1")

                    fasta_file = element.text
                #print(fasta_file)
        if connection:
            #fasta_file is now a string
            fasta_file = fasta_file.splitlines()
            info = fasta_file[0].strip('>')
            for i in range(1,len(fasta_file)):
                gene_sequence+=fasta_file[i]

            #if we have the expression same procedure except that now we have only one gene sequence
            if request.POST.get('expression'):
                expression = request.POST.get('expression')
                print(expression)
                if(gene_sequence.find(expression))!=-1:
                    locations = [m.start() for m in re.finditer(expression, gene_sequence)]
                    #print(info[i])
                    title = info
                    #for the plot
                    for location in locations:
                        features.append(GraphicFeature(start=location+0.5, end=location+len(expression)+0.5, strand=+1, color="#ffd700",label=expression))
                    record = GraphicRecord(sequence_length=len(gene_sequence), features=features)
                    #record = record.crop((locations[0],locations[-1]+len(expression)+1))
                    ax, _ = record.plot(figure_width=30)
                    if protein_id:
                        figure_name = 'sequence_and_translation_ncbi'+protein_id+expression+'.png'
                    elif nucleo_id:
                        figure_name = 'sequence_and_translation_ncbi'+nucleo_id+expression+'.png'
                    ax.figure.savefig('myapp/static/'+figure_name, bbox_inches='tight')
            elif request.POST.get('regex'):
                expression = request.POST.get('regex')
                expression = re.compile(expression)
                matches = re.findall(expression, gene_sequence)
                matches = set(matches)
                matches = list(matches)
                #print(matches)
                exact_matches=[]
                if matches!=[]:
                    if type(matches[0]) is tuple:
                        for match in matches:
                            exact_matches.append(match[0])
                    else:
                        exact_matches = matches
                    print(exact_matches)
                    for match in exact_matches:
                        locations+=[m.start() for m in re.finditer(match, gene_sequence)]
                        graph_locations = [m.start() for m in re.finditer(match, gene_sequence)]
                        for graph_location in graph_locations:
                            features.append(GraphicFeature(start=graph_location+0.5, end=graph_location+len(match)+0.5, strand=+1, color="#ffd700",label=match))
                    record = GraphicRecord(sequence_length=len(gene_sequence), features=features)
                    #record = record.crop((min(locations),max(locations)+len(max(exact_matches, key = len))+1))
                    ax, _ = record.plot(figure_width=30)
                    if protein_id:
                        figure_name = 'sequence_and_translation_ncbi'+protein_id+expression+'.png'
                    elif nucleo_id:
                        figure_name = 'sequence_and_translation_ncbi'+nucleo_id+expression+'.png'
                    ax.figure.savefig('myapp/static/'+figure_name, bbox_inches='tight')
                    title = info
    return render(request,'ncbi.html',{'title':title,'locations':locations,'figure_name':figure_name,'connection':connection,'posted':posted})




'''
When we get the fasta format from Uniprot by providing the protein_id
The text file is directly accesible from this link: https://www.uniprot.org/uniprot/P48740.fasta
>sp|P48740|MASP1_HUMAN Mannan-binding lectin serine protease 1 OS=Homo sapiens OX=9606 GN=MASP1 PE=1 SV=3
MRWLLLYYALCFSLSKASAHTVELNNMFGQIQSPGYPDSYPSDSEVTWNITVPDGFRIKL
'''
#For uniprot
def uniprot(request):
    info=''
    gene_sequence=''
    title=''
    locations=[]
    expression = ''
    features = []
    protein_id=''
    figure_name = ''
    connection = True
    posted = False
    if request.method == 'POST':
        posted = True
        #get the url with the protein_id
        protein_id = request.POST.get("id")
        try:
            file = requests.get('https://www.uniprot.org/uniprot/'+protein_id+'.fasta')
        except ConnectionError:
            print ('Failed to open url.')
            connection = False
        else:
            fasta_file = file.content
            fasta_file = fasta_file.decode('utf-8')
            fasta_file = fasta_file.splitlines()
            info = fasta_file[0].strip('>')
            for i in range(1,len(fasta_file)):
                gene_sequence+=fasta_file[i]

        if connection:
            #if we have the expression same procedure except that now we have only one gene sequence
            if request.POST.get('expression'):
                expression = request.POST.get('expression')
                print(expression)
                if(gene_sequence.find(expression))!=-1:
                    locations = [m.start() for m in re.finditer(expression, gene_sequence)]
                    #print(info[i])
                    title = info
                    for location in locations:
                        features.append(GraphicFeature(start=location+0.5, end=location+len(expression)+0.5, strand=+1, color="#ffd700",label=expression))
                    record = GraphicRecord(sequence_length=len(gene_sequence), features=features)
                    #record = record.crop((locations[0],locations[-1]+len(expression)+1))
                    ax, _ = record.plot(figure_width=30)
                    figure_name = 'sequence_and_translation_uniprot'+protein_id+expression+'.png'
                    ax.figure.savefig('myapp/static/'+figure_name, bbox_inches='tight')
            elif request.POST.get('regex'):
                expression = request.POST.get('regex')
                expression = re.compile(expression)
                matches = re.findall(expression, gene_sequence)
                matches = set(matches)
                matches = list(matches)
                #print(matches)
                exact_matches=[]
                if matches!=[]:
                    if type(matches[0]) is tuple:
                        for match in matches:
                            exact_matches.append(match[0])
                    else:
                        exact_matches = matches
                    print(exact_matches)
                    for match in exact_matches:
                        locations+=[m.start() for m in re.finditer(match, gene_sequence)]
                        graph_locations = [m.start() for m in re.finditer(match, gene_sequence)]
                        for graph_location in graph_locations:
                            features.append(GraphicFeature(start=graph_location+0.5, end=graph_location+len(match)+0.5, strand=+1, color="#ffd700",label=match))
                    record = GraphicRecord(sequence_length=len(gene_sequence), features=features)
                    #record = record.crop((min(locations),max(locations)+len(max(exact_matches, key = len))+1))
                    ax, _ = record.plot(figure_width=30)
                    figure_name = 'sequence_and_translation_uniprot'+protein_id+str(expression)+'.png'
                    ax.figure.savefig('myapp/static/'+figure_name, bbox_inches='tight')
                    title = info

    return render(request,'uniprot.html',{'title':title,'locations':locations,'figure_name':figure_name, 'connection':connection,'posted':posted})
