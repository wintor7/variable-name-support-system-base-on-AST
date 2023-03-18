import numpy as np
import networkx as nx
from typing import List
from karateclub.estimator import Estimator
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
#from karateclub.utils.treefeatures import WeisfeilerLehmanHashing
from MyWeisfeilerLehaman import WeisfeilerLehmanHashing
import csv
import pandas as pd
import newTry.combineAst as cA


def match_graphs(graph, graphs): 
  """
  Try to find graph of same variable.
  If exist, return the search result.
  else return None
  """
  for search in graphs:
    if graph.graph == search.graph:
      return search
  return None

def WLchange(graphs, wl_iterations, attributed, erase_base_features):
    """
    extracting feature by WL relabelling and setting tag
    """
    documents = [
    WeisfeilerLehmanHashing(
        graph, wl_iterations, attributed, erase_base_features
    )
    for graph in graphs
    ]

    documents = [
        doc.get_graph_features() for i, doc in enumerate(documents)
    ]
    return documents

class Graph2Vec(Estimator):
    r"""An implementation of `"Graph2Vec" <https://arxiv.org/abs/1707.05005>`_
    from the MLGWorkshop '17 paper "Graph2Vec: Learning Distributed Representations of Graphs".
    The procedure creates Weisfeiler-Lehman tree features for nodes in graphs. Using
    these features a document (graph) - feature co-occurence matrix is decomposed in order
    to generate representations for the graphs.

    The procedure assumes that nodes have no string feature present and the WL-hashing
    defaults to the degree centrality. However, if a node feature with the key "feature"
    is supported for the nodes the feature extraction happens based on the values of this key.

    Args:
        wl_iterations (int): Number of Weisfeiler-Lehman iterations. Default is 2.
        attributed (bool): Presence of graph attributes. Default is False.
        dimensions (int): Dimensionality of embedding. Default is 128.
        workers (int): Number of cores. Default is 4.
        down_sampling (float): Down sampling frequency. Default is 0.0001.
        epochs (int): Number of epochs. Default is 10.
        learning_rate (float): HogWild! learning rate. Default is 0.025.
        min_count (int): Minimal count of graph feature occurrences. Default is 5.
        seed (int): Random seed for the model. Default is 42.
        erase_base_features (bool): Erasing the base features. Default is False.
        mode: range of AST. default is 1. 1: line of var; 2:line of var & loop of var; 3:line of var & function of var; 4:line of var & loop of var & function of var
    """

    def __init__(
        self,
        wl_iterations: int = 2,
        attributed: bool = False,
        dimensions: int = 128,
        workers: int = 4,
        down_sampling: float = 0.0001,
        epochs: int = 10,
        learning_rate: float = 0.025,
        min_count: int = 5,
        seed: int = 42,
        erase_base_features: bool = False,
        mode:int = 1
    ):

        self.wl_iterations = wl_iterations
        self.attributed = attributed
        self.dimensions = dimensions
        self.workers = workers
        self.down_sampling = down_sampling
        self.epochs = epochs
        self.learning_rate = learning_rate
        self.min_count = min_count
        self.seed = seed
        self.erase_base_features = erase_base_features
        self.graph_note = []
        self.mode = mode



    def fit(self, graphs: List[nx.classes.graph.Graph], pkg_path, loop_graphs: List[nx.classes.graph.Graph], def_graphs: List[nx.classes.graph.Graph]):
        """
        Fitting a Graph2Vec model.

        Arg types:
            * **graphs** *(List of NetworkX graphs)* - The graphs to be embedded.
            pkg_path: the save path of model
            loop_graphs: the graph of variable's AST that range of loop when mode is 2 or 4
            def_graphs: the graph of variable's AST that range of function when mode is 3 or 4
        """
        self._set_seed() 
        print(len(graphs))     
        graphs = self._check_graphs(graphs)
        print(len(graphs))
        self.save_graph(graphs)

        if self.mode == 1:
            documents = WLchange(graphs, self.wl_iterations, self.attributed, self.erase_base_features)
    
        elif self.mode == 2:
            documents = WLchange(graphs, self.wl_iterations, self.attributed, self.erase_base_features)
            for i in range(len(graphs)):
                loop = match_graphs(graphs[i], loop_graphs)
                documents[i].append('for')
                if loop:
                    loop = WeisfeilerLehmanHashing(loop, 2, True, False)
                    loop = loop.get_graph_features()
                    for j in range(len(loop)):
                        documents[i].append(loop[j])
                else:
                    documents[i].append('')
                 
        elif self.mode == 3:
            documents = WLchange(graphs, self.wl_iterations, self.attributed, self.erase_base_features)
            for i in range(len(graphs)):
                defa = match_graphs(graphs[i], def_graphs)
                documents[i].append('def')
                if defa:
                    defa = WeisfeilerLehmanHashing(defa, 2, True, False)
                    defa = defa.get_graph_features()
                    for j in range(len(defa)):
                        documents[i].append(defa[j])
                else:
                    documents[i].append('')

        elif self.mode == 4:
            documents = WLchange(graphs, self.wl_iterations, self.attributed, self.erase_base_features)
            for i in range(len(graphs)):
                loop = match_graphs(graphs[i], loop_graphs)
                documents[i].append('for')
                if loop:
                    loop = WeisfeilerLehmanHashing(loop, 2, True, False)
                    loop = loop.get_graph_features()
                    for j in range(len(loop)):
                        documents[i].append(loop[j])
                else:
                    documents[i].append('')
                 
                defa = match_graphs(graphs[i], def_graphs)
                documents[i].append('def')
                if defa:
                    defa = WeisfeilerLehmanHashing(defa, 2, True, False)
                    defa = defa.get_graph_features()
                    for j in range(len(defa)):
                        documents[i].append(defa[j])
                else:
                    documents[i].append('')

        print(documents[8980])
        documents = [
            TaggedDocument(words=doc, tags=[str(i)])
            for i, doc in enumerate(documents)
        ]
        print(documents[8980])

        model = Doc2Vec(
            documents,
            vector_size=self.dimensions,
            window=0,
            min_count=self.min_count,
            dm=1,
            sample=self.down_sampling,
            workers=self.workers,
            epochs=self.epochs,
            alpha=self.learning_rate,
            seed=self.seed,
        )

        model.save(pkg_path)      #save the model 


        self._embedding = [model.docvecs[str(i)]
                           for i, _ in enumerate(documents)]

    def get_embedding(self) -> np.array:
        r"""Getting the embedding of graphs.

        Return types:
            * **embedding** *(Numpy array)* - The embedding of graphs.
        """
        return np.array(self._embedding)


        
    def infer_vector(self, graph, alpha=None, min_alpha=None, epochs=None, pkg_path='model/train_model.model'):
    """
    get the doc of graph and change to vector by model was trained
    """

    model = Doc2Vec.load(pkg_path)
    return model.infer_vector(graph, alpha, min_alpha, epochs)  


    def most_similar(self, positive=None, negative=None, topn=10, clip_start=0, clip_end=None,
            restrict_vocab=None, indexer=None, pkg_path='model/train_model.model'):
        
        """
        To find the similar vector
        """
        model = Doc2Vec.load(pkg_path)
        sim = model.dv.most_similar(positive, negative, topn, clip_start, clip_end, restrict_vocab, indexer)
        data = self.load_graph()
        result = [
            (sim[no][0], data.loc[int(sim[no][0])][0], sim[no][1])
            for no in range(len(sim)) 
        ]    
        return result



    def train(self, graphs, pkg_path): 
        model = Doc2Vec.load(pkg_path)
        self._set_seed()
        self.save_graph(graphs)
        graphs = self._check_graphs(graphs)
        documents = [
            WeisfeilerLehmanHashing(
                graph, self.wl_iterations, self.attributed, self.erase_base_features
            )
            for graph in graphs
        ]
        documents = [
            TaggedDocument(words=doc.get_graph_features(), tags=[str(i)])
            for i, doc in enumerate(documents)
        ]
        model.train(documents, total_examples=model.corpus_count, epochs=model.epochs)
        model.save(pkg_path)


    def save_graph(self, graphs):   
        """
        To save the model
        """

        graph_note = []
        for i in range(len(graphs)):
            graph_note.append(graphs[i].graph)
        csv_path = "/Users/wintor7/Research/graph_note.csv"
        graph_notes = [str(list(graph_note[i].values())) for i in range(len(graph_note))]
        tmp = pd.DataFrame({"label":graph_notes})
        tmp.to_csv(csv_path, mode= 'a', index=False, header=False)



    def load_graph(self):
        """
        To load the model
        """
        csv_path = "/Users/wintor7/Research/graph_note.csv"
        with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as f:
            data = pd.read_csv(csv_path)

        return data

    def _check_graphs(self, graphs: List[nx.classes.graph.Graph]):
        return super()._check_graphs(graphs)




        