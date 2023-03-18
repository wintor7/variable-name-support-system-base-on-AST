import networkx as nx
import matplotlib.pyplot as plt
import ast


def create_node_lib():
  """
  To prepare number of AST node. 
  """  
  path = 'node_lib.txt'
  with open(path,'r') as file:
    file = file.read()
    node_list = file.rstrip().split(', ')
  node_to_id = {}
  id_to_node = {}
  for node  in node_list:
    if node not in node_to_id:
      new_id = len(node_to_id)
      node_to_id[node] = new_id
      id_to_node[new_id] = node
  
  return node_to_id, id_to_node

def create_graph(node, node_to_id, G, str_to_node, root):
  """
  To create AST graph of variable.
  params:
    node: first node that is created.
    node_to_id: the corpus of AST node
    G: graph of AST
    str_to_node: the name of node
    root: the begin node of graph
  """
  i = len(str_to_node)
  j = root
  try: 
    if str_to_node[j] == None:
      str_to_node[j] =  node_to_id[type(node).__name__] 
  except:
    str_to_node[j] =  node_to_id[type(node).__name__]
  if str_to_node[j] !=  node_to_id[type(node).__name__]:
    str_to_node[j] =  node_to_id[type(node).__name__]

  for child_node in ast.iter_child_nodes(node):
    i = len(str_to_node)
    str_to_node[i] = node_to_id[type(child_node).__name__]
    G.add_edges_from({(j , i)})
    create_graph(child_node, node_to_id, G, str_to_node, i)


def name_corpus(list, name_to_id, id_to_name):
  """
  To change AST node to number node.
  param:
    list: The AST list of input variable 
    name_to_id: To prepare number of AST node of input variable.
    id_to_name: To prepare name that match with AST node.
  """
  for name in list:
    if name not in name_to_id:
      new_id = len(name_to_id)
      name_to_id[name] = new_id
      id_to_name[new_id] = name

  return name_to_id, id_to_name





 
 