#!/usr/bin/env python3

import os
import pdfrw
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



def parse_template(path):
    parsed = toml.load(path)

    template_kv = {}
    key_order = []

    if 'field_name' not in parsed:
        parsed['field_name'] = []

    for kv in  parsed['field_name']:
        key_order.append(kv['id'])
        template_kv[kv['id']] =   kv['name']

    return template_kv, key_order

def write_template(path, temp, order):
    fn = []
    for k in order:
        kv = {'id':k, 'name':temp[k]}
        fn.append(kv)
    
    to_dump = {'field_name':fn}

    with open(path, 'w') as f:
        toml.dump(to_dump, f )



def complete_template(template_path, source_path):
    temp_kv, temp_order = parse_template(template_path)

    fields = get_all_keys(source_path)
    for field in fields:
        if field not in temp_order:
            temp_order.append(field)
            temp_kv[field] = random_word()

    write_template(template_path, temp_kv, temp_order)


# sudo apt install wamerican-small
wordlist = []
with open('/usr/share/dict/american-english-small', 'r') as f:
    wordlist = [x.strip() for x in f.readlines()]
    
def random_word():
    ans = wordlist[random.randint(0, len(wordlist)-1)]
    if "'" in ans:
        return random_word()
    return ans



if __name__ == '__main__':
    in_path = '2017-irs/f1040--2017.pdf'
    template_path = '2017-irs/f1040--2017.template.toml'
    out_path = '2017-irs/f1040--2017.out.pdf'


    complete_template(template_path, in_path)
    temp_kv, temp_order = parse_template(template_path)
    fill_fn = lambda x : temp_kv[x]
    fill_pdf(in_path, out_path, fill_fn)
