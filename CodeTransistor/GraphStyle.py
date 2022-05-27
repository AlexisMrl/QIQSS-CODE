import re
import glob
import sys
import os.path
import pylab
from operator import truediv
from pylab import*
from matplotlib.widgets import Slider, Button, RadioButtons
from matplotlib.widgets import Slider, Button, RadioButtons
from statistics import stdev 

def yes_or_no():
	while "the answer is invalid":

		try:
			reply = str(raw_input('Are you sure you want to save the graph, it could erase previous ?'+' (y/n): ')).lower().strip()
		except:
			reply = str(input('Are you sure you want to save the graph, it could erase previous ?'+' (y/n): ')).lower().strip()
		if reply[0] == 'y':
			return True
		if reply[0] == 'n':
			return False

def graph(fig,path=None,name=None, xlabel=None, ylabel=None, title=None, legend=None, col=1,
		 xtick=None, xticklabel=None, xlim=None,ylim=None,figsize=[6,5],fontsize=16,labelsize=14,
		 save=False, format='png',ax=None,bordelinewidth=1.5):
	if ax is None:
		ax=fig.gca()
	ax.axes.tick_params(labelsize=labelsize)
	fig.set_size_inches(figsize)
	for axis in ['top','bottom','left','right']:
 		 ax.spines[axis].set_linewidth(bordelinewidth)
	if xlabel is not None:
		ax.set_xlabel(xlabel,fontsize=fontsize)
	if ylabel is not None:
		ax.set_ylabel(ylabel,fontsize=fontsize)
	if title is not None:
		ax.set_title(title, fontsize=fontsize)
	if legend is not None:
		ax.legend(legend,fontsize=fontsize, ncol=col,loc=0)
	# else:
	# 	ax.legend(fontsize=fontsize, ncol=col,loc=0)
	if xtick is not None:
		plt.xticks(xtick, xticklabel)
	if xlim is not None:
		plt.xlim(xlim)
	if ylim is not None:
		plt.ylim(ylim)
	# fixed_aspect_ratio_loglog(ax,1)
	plt.tight_layout()

	
	if save==True:
		save=yes_or_no()
	if save==True:
			filename=path+'\\'+name+'.'+format
			plt.savefig(filename,dpi=500,transparent=True) 


def graphPy3(fig,path=None,name=None, xlabel=None, ylabel=None, title=None, legend=None, col=1,
		 xtick=None, xticklabel=None, xlim=None,ylim=None,figsize=[6,5],fontsize=12,labelsize=10,
		 save=False, png=True,aspect=True):
	ax=fig.gca()
	ax.axes.tick_params(labelsize=labelsize)
	fig.set_size_inches(figsize)
	if xlabel is not None:
		ax.set_xlabel(xlabel,fontsize=fontsize)
	if ylabel is not None:
		ax.set_ylabel(ylabel,fontsize=fontsize)
	if title is not None:
		ax.set_title(title, fontsize=fontsize)
	if legend is not None:
		ax.legend(legend,fontsize=fontsize, ncol=col,loc=0)
	if xtick is not None:
		plt.xticks(xtick, xticklabel)
	if xlim is not None:
		plt.xlim(xlim)
	if ylim is not None:
		plt.ylim(ylim)
	# if aspect:
		# ax.set_box_aspect(1)	
	plt.tight_layout()

	if save==True:
		save=yes_or_no()
		if save==True:
			if png==True:
				filename=path+'\\'+name+'.png'
				plt.savefig(filename,dpi=300, transparent=True) 
			else:
				filename=path+'\\'+name+'.svg'
				plt.savefig(filename,dpi=300) 
		


def fixed_aspect_ratio_loglog(ax,ratio):
    '''
    Set a fixed aspect ratio on matplotlib loglog plots 
    regardless of axis units
    '''
    xvals,yvals = ax.axes.get_xlim(),ax.axes.get_ylim()

    xrange = log(xvals[1])-log(xvals[0])
    yrange = log(yvals[1])-log(yvals[0])
    gca().set_aspect(ratio*(xrange/yrange), adjustable='box')


