#!/usr/bin/env python3

from toml import ordered as toml_ordered
from collections import OrderedDict
import os
import pdfrw
import glob
import random
import toml



ANNOT_KEY = '/Annots'
ANNOT_FIELD_KEY = '/T'
SUBTYPE_KEY = '/Subtype'
WIDGET_SUBTYPE_KEY = '/Widget'


def get_all_keys(input_pdf_path):
    template_pdf = pdfrw.PdfReader(input_pdf_path)
    
    annotations = []
    for page in template_pdf.pages:
        annotations += page[ANNOT_KEY]

    all_keys = []
    for annotation in annotations:
        if annotation[SUBTYPE_KEY] == WIDGET_SUBTYPE_KEY:

            if annotation[ANNOT_FIELD_KEY]:
                key = annotation[ANNOT_FIELD_KEY][1:-1]
                all_keys.append(key)


    return all_keys

def fill_pdf(input_pdf_path, output_pdf_path, lookup_fn):
    template_pdf = pdfrw.PdfReader(input_pdf_path)
    
    annotations = []
    for page in template_pdf.pages:
        annotations += page[ANNOT_KEY]

    for annotation in annotations:
        if annotation[SUBTYPE_KEY] == WIDGET_SUBTYPE_KEY:

            if annotation[ANNOT_FIELD_KEY]:
                key = annotation[ANNOT_FIELD_KEY][1:-1]

                fill_with = lookup_fn(key)
                annotation.update(
                    pdfrw.PdfDict(V='{}'.format(fill_with))
                )

    template_pdf.Root.AcroForm.update(pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject('true')))

    pdfrw.PdfWriter().write(output_pdf_path, template_pdf)



def parse_template(path, header='field_name'):
    if not os.path.exists(path):
        print('creating file', path)
        with open(path, "w+") as f:
            f.write('\n')


    parsed = toml.load(path , decoder = toml_ordered.TomlOrderedDecoder())

    if header not in parsed:
        parsed[header] = OrderedDict()

    return parsed[header]

def write_template(path, temp, header = 'field_name'):
    to_dump = {header:temp}

    # workaround for bug that should be fixed. see comments on https://github.com/uiri/toml/pull/248
    fstring = toml.dumps(to_dump, encoder = toml_ordered.TomlOrderedEncoder())
    with open(path, 'w') as f:
        f.write(fstring)



def complete_template(template_path, source_path):
    temp_kv = parse_template(template_path)

    fields = get_all_keys(source_path)
    for field in fields:
        if field not in temp_kv.keys():
            temp_kv[field] = random_word()

    write_template(template_path, temp_kv)


# sudo apt install wamerican-small
wordlist = []
with open('/usr/share/dict/american-english-small', 'r') as f:
    wordlist = [x.strip() for x in f.readlines()]
    
def random_word():
    ans = wordlist[random.randint(0, len(wordlist)-1)]
    if "'" in ans:
        return random_word()
    if len(ans) <= 2:
        return random_word()
    if ans.lower() != ans:
        return random_word()
    return ans


def demo_keys(template_path, pdf_in, pdf_out):
    temp_kv = parse_template(template_path)
    fill_fn = lambda x : temp_kv[x]
    fill_pdf(pdf_in, pdf_out, fill_fn)


def complete_values(template_path, values):
    temp_kv = parse_template(template_path)
    value_kv = parse_template(values, "values")

    for k in temp_kv.keys():
        if k not in value_kv:
            value_kv[k] =           ''
            print('adding new field', k)

    for k in value_kv.keys():
        if k not in temp_kv:
            del (value_kv, k)
            print('KILLING UNKNOWN FIELD', k ,value_kv[k])

    write_template(values, value_kv, 'values')


def process_form(template_path, values, pdf_in, pdf_out_demo, pdf_out_filled):
    complete_template(template_path, pdf_in)
    demo_keys(template_path, pdf_in, pdf_out_demo)
    complete_values(template_path, values)


if __name__ == '__main__':
    source_dir = '2017-irs/'
    value_dir = '../taxes/2017-irs/'
    out_dir = '../taxes/2017-irs/output/'

    forms = glob.glob(source_dir+'*.pdf')
    for form in forms:
        filename = form.split('/')[-1]
        filename_prefix = ''.join(filename.split('.')[:-1])
        print(filename, filename_prefix)
        filename_demo = filename_prefix + '.demo.pdf'
        filename_filled = filename_prefix + '.filled.pdf'
        filename_template = filename_prefix + '.template.toml'
        filename_values = filename_prefix + '.toml'

        process_form(source_dir + filename_template,
                     value_dir+ filename_values,
                     form,
                     out_dir + filename_demo,
                     out_dir + filename_filled)



