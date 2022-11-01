"""
１、レポットコード内すべて関数名と変数名を抽出する。
２、関数に対してローカル変数及び関して構文木を抽出する。

"""

import ast
import builtins
from cmath import e
from distutils.log import error
from tkinter import E

import glob
import pandas as pd
import keyword
import networkx as nx
import node_to_vec as n2v


class CodeTransformer(ast.NodeTransformer):
  '''
  params:

  '''
  def __init__(self):
    self.func_name, self.var_name, self.for_name = [], [], []  #to save name of function, var and for 
    self.stu_id = ""                                           #to save student_id
    self.var_in_func = {}                                      # to save var in which function without subfunction
    self.name_line = {}                                        # to save var in which line
    self.target_var = None                                     # which target var is tracked at the moment
    self.func = ""                                             # which function is used at the moment
    self.check_func_sublist = {}                               # to save subfunction in which function
    self.namefunc_line = {}

  #ASTの走査

  '''def visit_Name(self, node):
    self.get_var_name(node.id)
    self.generic_visit(node)
    return node'''

  def visit_FunctionDef(self, node):
    self.func = node.name
    self.get_func_name(node.name)
    self.generic_visit(node)
    self.get_var_in_func(node)
    #self.merge_func(node)
    return node
  
  def visit_For(self, node):
    try:
      self.get_for_name(node.target.id)
    except:
      pass 
    self.generic_visit(node)
    return node  

  #for文の臨時変数を抽出する
  def get_for_name(self, for_id:str):
    if for_id not in self.for_name :
      self.for_name.append(for_id)  #for文の臨時変数を抽出する
    if for_id in self.var_name:
      self.var_name.remove(for_id)  #変数名中保存したfor文の臨時変数を削除する

  #変数名を抽出する
  def get_var_name(self, var_id:str):
    if var_id not in ( set(keyword.kwlist) | set(dir(builtins))):  #キーワードまたは関数名かどうかを判定する
      if var_id in set(self.func_name):
        if self.func not in self.check_func_sublist.keys():
          self.check_func_sublist[self.func] = [var_id]
        elif var_id not in self.check_func_sublist[self.func]:
          self.check_func_sublist[self.func].append(var_id)
      elif var_id not in self.for_name:     #for文の臨時変数かどうかを判定する
        self.var_name.append(var_id)
        return var_id

  #関数名を抽出する
  def get_func_name(self, func_id:str):
    if func_id not in self.func_name:
      self.func_name.append(func_id)

  #各関数内変数名を抽出する
  def get_var_in_func(self, node):
    func_name = self.func
    for child in ast.iter_child_nodes(node):
      if type(child).__name__ == "Name":
        var_id = self.get_var_name(child.id)
        self.get_var_name_line(child)
        if var_id != None:
          if func_name not in  self.var_in_func.keys():
            self.var_in_func[func_name] = [var_id]
          elif child.id not in self.var_in_func[func_name]:
            self.var_in_func[func_name].append(var_id)
      self.get_var_in_func(child)

  def get_var_name_line(self, node):
    if hasattr(node, 'id'):
      for key, value in self.var_in_func.items():
        if key in self.name_line.keys():
          var_line = self.name_line[key]
        else:
          var_line = {}
        if self.func == key:
          if node.id in value:
            if type(node.id) == type(""):
              if node.id not in var_line.keys():
                var_line[node.id] = [node.lineno] 
              elif node.lineno != var_line[node.id]:
                var_line[node.id].append(node.lineno)
          self.name_line[key] = var_line
    else:
      pass
      



 

  #対応した変数の構文木を抽出
  def track_line(self, node, line):
    if hasattr(node, "lineno"):
      if line != node.lineno:
        for child in ast.iter_child_nodes(node):
          self.track_line(child,line)  
      else:
        #print(node.lineno, node)
        self.target_var = node
        pass
    else:
      for child in ast.iter_child_nodes(node):
          self.track_line(child,line) 


#各関数内変数名の頻度を統計する
def counter(dict_func, var_in_func):
  for key, value in var_in_func.items():
    if key in dict_func.keys():
      var_counter = dict_func[key]
    else:
      var_counter = {}
    for word in value:
      if word not in var_counter.keys():
        var_counter[word] = 1
      elif word in var_counter.keys():
        var_counter[word] += 1
    dict_func[key] = var_counter
  return dict_func  

def merge_func(check_func, var_in_func, func_list, id):
  for func_name in func_list:
    if func_name in check_func.keys():
      for i in check_func[func_name]:
        try:
          for j in var_in_func[i]: 
            if j not in var_in_func[func_name]:       
              var_in_func[func_name].append(j)
          del var_in_func[i] 
        except Exception as r:
          pass

def filter_var(dict_func):
  for key, value in list(dict_func.items()):
    for var in list(value.keys()):
      if value[var] <= 5:
        del value[var]
    if dict_func[key]:
      pass
    else:
      del dict_func[key]


if __name__ == "__main__":
  var, for_var, func_var, func_params, func_return = {}, {}, {}, {}, {}
  dict_func, var_counter = {},{}
  var_to_id, func_to_id = {},{}
  id_to_var, id_to_func = {},{}
  node_to_id = {}
  id_to_node = {}

  path = '/Users/wintor7/report7/'

  filenames = glob.glob(path + 'report7**/**/report7.py')
  print(len(filenames))
  for file in filenames:
    try:
      student_id = file.split("/")[-2]
      with open(file, 'r') as fh:
        content = fh.read()

        #抽取AST
      r_node = ast.parse(content)

      transformer = CodeTransformer()
      transformer.stu_id = student_id
      r_node = transformer.visit(r_node)
      merge_func(transformer.check_func_sublist, transformer.var_in_func, transformer.func_name, transformer.stu_id)
      dict_func = counter(dict_func, transformer.var_in_func)
    except:
      continue
  
  filter_var(dict_func)
      #print(student_id, transformer.var_in_func)

  print('dict_func: ', dict_func)
  graphs = []
  for file in filenames:
    student_id = file.split("/")[-2]
    with open(file, 'r') as fh:

      content = fh.read()

  #抽取AST
    print(student_id)
    r_node = ast.parse(content)

    transformer = CodeTransformer()
    transformer.stu_id = student_id
    r_node = transformer.visit(r_node)

    func_list = list(transformer.var_in_func.keys())
    var_list = []
    for i,v in enumerate(transformer.var_in_func):
      for i in transformer.var_in_func[v]:
        var_list.append(i)
    
    name_line = transformer.name_line

    print('name_line: ',name_line)

    temp = {}
    for key in dict_func.keys():        #确认是否为常见变量名称
      for var in dict_func[key].keys():
        try:
          if var in name_line[key].keys():
            temp[var] = name_line[key][var]
          else:
            continue
        except KeyError:
          continue
    print('temp:',temp)

    name_line = temp     
    print("delete:" + transformer.stu_id )    
    print(name_line)     
    node_list = {}
    for key in name_line.keys():          #
      #print(key)
      for i in name_line[key]:
        transformer.track_line(r_node, i)
        if key not in node_list.keys():
          node_list[key] = [transformer.target_var]
        elif transformer.target_var not in node_list[key]:
          node_list[key].append(transformer.target_var)
    print('node_list:', node_list)

    node_to_id, id_to_node = n2v.create_node_lib() 
    var_to_id, id_to_var = n2v.name_corpus(var_list, var_to_id, id_to_var)
    func_to_id, id_to_func = n2v.name_corpus(func_list, func_to_id, id_to_func)


    num = 0
    var_in_func = transformer.var_in_func
    print('var_in_func: ', var_in_func)
    for func in var_in_func.keys():
      if func in dict_func.keys():
        label1 = func
        for var in var_in_func[func]:
          if var in dict_func[func].keys():
            label2 = var
            graph = nx.DiGraph(label1 = label1, label2 = label2)
            str_to_node = {}
            try:
              for var_node in node_list[var]:
                root = len(str_to_node)
                n2v.create_graph(var_node, node_to_id, graph, str_to_node, root)
                for node in graph.nodes():
                  graph.nodes[node]['feature'] = str_to_node[node]
                root += 1
              #nx.write_gpickle(graph,'/Users/wintor7/Research/graphset/' + str(num) + '.gpickle')  
              num += 1
            except KeyError:
              continue
          else:
            continue

        graphs.append(graph)

  print(len(graphs))


      






         
