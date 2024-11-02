# -*- coding: utf-8 -*-


def find_sub_list(sl,l):
   sll=len(sl)
   for ind in range(0,len(l)):
       if l[ind:ind+sll]==sl:
           return ind,ind+sll-1

           
# dummy method, not doing anything, still called in all classes
def encode_german_characters(string):
    return string
        
# new method, call for pydot only        
def encode_german_chars(string):
    de_ascii = [
        ('ä', 'ae'),
        ('Ä', 'Ae'),
        ('ö', 'oe'),
        ('Ö', 'Oe'),
        ('ü', 'ue'),
        ('Ü', 'Ue'),
        ('ß', 'ss')
    ]
    for rep in de_ascii:
        string = string.replace(rep[0], rep[1])
    return string.encode('ascii','ignore')