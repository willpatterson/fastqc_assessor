
# Import necessary libraries:
import csv
import os
import subprocess
import zipfile

# List modules used by FastQC:
modules = ['Basic_Statistics',
           'Per_base_sequence_quality',
           'Per_sequence_quality_scores',
           'Per_base_sequence_content',
           'Per_base_GC_content',
           'Per_sequence_GC_content',
           'Per_base_N_content',
           'Sequence_Length_Distribution',
           'Sequence_Duplication_Levels',
           'Overrepresented_sequences',
           'Kmer_Content']

# Set dict to convert module results to integer scores:
scores = {'pass': 1,
          'warn': 0,
          'fail': -1}

# Get current working directory:
cwd = os.getcwd()

# Get list of '_fastqc.zip' files generated by FastQC:
files = [file for file in os.listdir(cwd) if file.endswith('_fastqc.zip')]

# List to collect module scores for each '_fastqc.zip' file:
all_mod_scores = []

# Read fastqc_data.txt file in each archive:
for file in files:
    archive = zipfile.ZipFile(file, 'r') # open '_fastqc.zip' file
    members = archive.namelist() # return list of archive members
    fname = [member for member in members if 'fastqc_data.txt' in member][0] # find 'fastqc_data.txt' in members
    data = archive.open(fname) # open 'fastqc_data.txt'

    ovseq_flag = False
    over_rep_lines = []

    mod_scores = [file]
    general_info = {'total_seq': 0, 'seq_len': 0, 'gc': 0, 'over_rep_lines': []} #Added Information to find for Amie
    # Get module scores for this file:
    for line in data:
        text = line.decode('utf-8')

        #Deals with pulling out Overrepresented sequences **Excluding No Hit**
        if '>>Overrepresented sequences' in text:
            ovseq_flag = True
        elif ovseq_flag == True and text.startswith('>>END_MODULE'):
            ovseq_flag = False
        elif ovseq_flag == True and not (text.startswith('#') or 'No Hit' in text):
            rep_line = text.replace('\t', ':')
            rep_line = rep_line.replace(',', '+')
            rep_line = rep_line.replace('\n', '')
            rep_line = rep_line.replace(' ', '-')
            general_info["over_rep_lines"].append(rep_line)

        #Deals with pulling out General information 
        elif text.startswith('Total Sequences'):
            general_info['total_seq'] = text.split('\t')[1][:-1]
        elif text.startswith('Sequence length'):
            general_info['seq_len'] = text.split('\t')[1][:-1]
        elif text.startswith('%GC'):
            general_info['gc'] = text.split('\t')[1][:-1]

        #Pulls out Mod scores
        if '>>' in text and '>>END' not in text:
            text = text.lstrip('>>').split()
            module = '_'.join(text[:-1])
            result = text[-1]
            mod_scores.append(scores[result])

    #Concat mod scores with general info
    mod_scores = mod_scores + [general_info['total_seq'],
                               general_info['seq_len'],
                               general_info['gc'],
                               '&&'.join(general_info['over_rep_lines'])]
    # Append to all module scores and general info to list:
    all_mod_scores.append(mod_scores)

    # close all opened files:
    data.close()
    archive.close()

# Write scores out to a CSV file:
with open('all_mod_scores.csv', 'w') as f:
    writer = csv.writer(f)
    for mod_scores in all_mod_scores:
        writer.writerow(mod_scores)
    f.close()
