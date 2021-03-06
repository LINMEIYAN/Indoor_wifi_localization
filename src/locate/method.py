import platform
import sys
import matplotlib.pyplot as plt
import numpy as np
import cnn_tf
from data_process import plot

PLATFORM = platform.system()

# pity for windows
'''
if PLATFORM == "Windows":
    reload(sys)
    sys.setdefaultencoding('gbk')
elif PLATFORM == "Darwin":
    pass
else:
    reload(sys)
    sys.setdefaultencoding('utf-8')
'''


def plot_pred(train_ds, test_ds, pred, title=None):
    pred = np.asarray(pred)
    print("pred.shape: {}".format(pred.shape))
    fig = plot(train_ds.pos, color="b")
    gt_mark = ["gt{0}_({1:.2f},{2:.2f})".format(i, test_ds.pos[i][0], test_ds.pos[i][1])
               for i in range(len(test_ds.pos))]
    pred_mark = ["pred{0}_({1:.2f},{2:.2f})".format(i, pred[i][0], pred[i][1])
                 for i in range(len(pred))]
    fig = plot(test_ds.pos, fig=fig, color="y", mark=gt_mark)
    fig = plot(pred, fig=fig, color="r", mark=pred_mark)
    if title is not None:
        plt.title(title)
    plt.xlabel("x")
    plt.ylabel("y")
    return fig

def compute_error(true_coords, pred_coords):
    error_coords = true_coords - pred_coords
    error = sum(map(np.linalg.norm, error_coords))
    return error

class kNN(object):
    """
    k nearest-neighbour matching algorithm 
    """

    def __init__(self, k, train_ds):
        self.k = k
        self.train_ds = train_ds

    def __call__(self, test_samples):
        coords = np.zeros([len(test_samples), 2], dtype=np.float32)
        for idx, vector in enumerate(test_samples):
            coords[idx] = self._locate(vector)

        return coords

    def _locate(self, vector):
        """
        internal locating function for one vector
        """
        ndary = self.train_ds.ndary
        dis_lst = [(np.linalg.norm(vector - ndary[i]), i) for i in range(self.train_ds.pos_num)]
        # sort using distance
        dis_lst.sort(key=lambda tup: tup[0])
        # NOTE: weight proportional to 1/distance
        kweight = [1. / (tup[0] + 10e-5) for tup in dis_lst[0:self.k]]
        kidx = [tup[1] for tup in dis_lst[0:self.k]]
        kcoords = [self.train_ds.pos[idx] for idx in kidx]
        # calculate the coordinates (x, y) using weighted sum
        weight_sum = sum(kweight)
        kweight = [weight / float(weight_sum) for weight in kweight]
        coord = np.zeros([2], dtype=np.float32)
        for i in range(self.k):
            coord = coord + kcoords[i] * kweight[i]

        return coord


class CNN(object):
    """
    convoluation neural network
    """

    def __init__(self, train_ds, weights_path=None):
        x_shape = [None] + list(train_ds.ndary.shape[1:]) + [1]
        y_shape = [None] + list(train_ds.pos.shape[1:])
        self.cnn = cnn_tf.CNN(x_shape, y_shape, "../cnn_data/ckpt", "../cnn_data/tsbd", 0.00001)
        self.cnn.initialize(weights_path)

    def __call__(self, test_samples):
        return self.cnn.test(test_samples)[0]


if __name__ == "__main__":
    # test, DO NOT run this
    assert len(sys.argv) == 3
    from dataset import Dataset

    with open(sys.argv[1], "r") as f:
        lines = [l.strip() for l in f.readlines()]
    ds = Dataset(lines)
    locater = kNN(int(sys.argv[2]), ds)
    print(locater(ds))
