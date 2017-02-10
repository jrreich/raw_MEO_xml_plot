import numpy as np
from matplotlib import pyplot as plt
from matplotlib import animation

#figFL = plt.figure('FL')
#figHI = plt.figure('HI')
MEOList = ['FL','HI']
Ant
def example_plot(ax, title,MEO, fontsize = 12):
    print ax[0] 
    ax[0].plot([1, 2])
    ax[0].locator_params(nbins=3)
    ax[0].set_xlabel('x-label', fontsize=fontsize)
    ax[0].set_ylabel('y-label', fontsize=fontsize)
    ax[0].set_title(title, fontsize=fontsize)

fig, axs = plt.subplots(6,2,sharex = True)
print axs.shape
titles = range(1,7)

[example_plot(ax,title,MEO, 24) for ax in axs for title in titles for MEO in MEOList] 

plt.show()

