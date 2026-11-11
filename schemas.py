"""Bounded JSON and the documented JSON Schema subset used by this package.

This is not a general JSON Schema implementation. Unsupported keywords fail.
"""
import json
import math
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent
MAX_BYTES=4*1024*1024
KEYWORDS={'$schema','$id','$defs','$ref','title','description','type','required','properties',
          'additionalProperties','items','minItems','maxItems','uniqueItems','minLength','maxLength',
          'minimum','maximum','minProperties','enum','const','pattern','oneOf','anyOf','allOf'}


def strict_json(raw):
    if isinstance(raw,bytes):raw=raw.decode('utf-8')
    if len(raw.encode('utf-8'))>MAX_BYTES:raise ValueError('JSON exceeds 4 MiB')
    def pairs(values):
        result={}
        for k,v in values:
            if k in result:raise ValueError('duplicate JSON key: '+k)
            result[k]=v
        return result
    def invalid(value):raise ValueError('nonfinite JSON number')
    def finite_float(value):
        number=float(value)
        if not math.isfinite(number):invalid(value)
        return number
    try:return json.loads(raw,object_pairs_hook=pairs,parse_constant=invalid,parse_float=finite_float)
    except RecursionError as exc:raise ValueError('JSON nesting exceeded') from exc


def read_json(path):
    with Path(path).open('rb') as stream:raw=stream.read(MAX_BYTES+1)
    return strict_json(raw)


def validate(value,schema,root=None,path='$',depth=0):
    if depth>50:raise ValueError('schema/data depth exceeded')
    root=schema if root is None else root
    if schema is True:return
    if schema is False:raise ValueError(path+': forbidden')
    if set(schema)-KEYWORDS:raise ValueError('unsupported schema keyword')
    if '$ref' in schema:
        ref=schema['$ref']
        if not ref.startswith('#/'):raise ValueError('only local schema references supported')
        target=root
        for key in ref[2:].split('/'):target=target[key]
        validate(value,target,root,path,depth+1)
    types={'object':lambda x:isinstance(x,dict),'array':lambda x:isinstance(x,list),
           'string':lambda x:isinstance(x,str),'integer':lambda x:type(x)is int,
           'number':lambda x:type(x)in(int,float),'boolean':lambda x:type(x)is bool,'null':lambda x:x is None}
    if 'type' in schema:
        ts=schema['type'] if isinstance(schema['type'],list) else [schema['type']]
        if not any(types[t](value) for t in ts):raise ValueError(path+': type')
    if 'const' in schema and (value!=schema['const'] or type(value)!=type(schema['const'])):raise ValueError(path+': const')
    if 'enum' in schema and not any(value==x and type(value)==type(x) for x in schema['enum']):raise ValueError(path+': enum')
    for keyword in ('oneOf','anyOf','allOf'):
        if keyword in schema:
            count=0
            for child in schema[keyword]:
                try:validate(value,child,root,path,depth+1);count+=1
                except ValueError:pass
            if (keyword=='oneOf' and count!=1) or (keyword=='anyOf' and count==0) or (keyword=='allOf' and count!=len(schema[keyword])):
                raise ValueError(path+': '+keyword)
    if isinstance(value,dict):
        if len(value)<schema.get('minProperties',0):raise ValueError(path+': object bounds')
        if set(schema.get('required',[]))-value.keys():raise ValueError(path+': required')
        props=schema.get('properties',{});extra=schema.get('additionalProperties',True)
        for k,v in value.items():validate(v,props.get(k,extra),root,path+'.'+k,depth+1)
    if isinstance(value,list):
        if len(value)<schema.get('minItems',0) or len(value)>schema.get('maxItems',100000):raise ValueError(path+': array bounds')
        if schema.get('uniqueItems') and len({json.dumps(x,sort_keys=True) for x in value})!=len(value):raise ValueError(path+': duplicates')
        for n,v in enumerate(value):validate(v,schema.get('items',True),root,path+f'[{n}]',depth+1)
    if isinstance(value,str):
        if len(value)<schema.get('minLength',0) or len(value)>schema.get('maxLength',MAX_BYTES):raise ValueError(path+': string bounds')
        if 'pattern' in schema and re.search(schema['pattern'],value) is None:raise ValueError(path+': pattern')
    if type(value) in (int,float):
        if value<schema.get('minimum',float('-inf')) or value>schema.get('maximum',float('inf')):raise ValueError(path+': numeric bounds')


def load_suite(path):
    suite=read_json(path);validate(suite,read_json(ROOT/'schemas/case.schema.json'))
    for case in suite['cases']:
        for event in case['events']:
            if event['op']=='grant' and (('parent' in event)!=('parent_epoch' in event)):
                raise ValueError('delegation requires both parent and parent_epoch')
    ids=[x['id'] for x in suite['cases']]
    if len(set(ids))!=len(ids):raise ValueError('duplicate case ID')
    return suite
