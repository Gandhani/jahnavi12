# -*- coding: utf-8 -*-
"""
Created on Sat Oct 20 13:49:29 2018

@author: anhol
"""

from __future__ import division

from .base import Dataset
import re
import numpy as np

from six import PY3
from .util import DocInherit
import inspect
from functools import wraps


class MetaFileDataset(Dataset):
    """MetaFileDataset is a thin layer between Dataset and FileDataset.
    This two-layer inheritance is required to make @classmethod decorators work.
    Practically speaking, that means that MetaFileDataset implements \
    expectation decorators, like `column_map_expectation` and `column_aggregate_expectation`, \
    and FileDataset implements the expectation methods themselves.
    """

    def __init__(self, *args, **kwargs):
        super(MetaFileDataset, self).__init__(*args, **kwargs)
        
        
    @classmethod
    
    def file_map_expectation(cls, func):
        """Constructs an expectation using file-map semantics.
        
        """
        if PY3:
            argspec = inspect.getfullargspec(func)[0][1:]
        else:
            argspec = inspect.getargspec(func)[0][1:]

        @cls.expectation(argspec)
        @wraps(func)
        def inner_wrapper(self, mostly=None, skip=None, result_format=None, *args, **kwargs):

            if result_format is None:
                result_format = self.default_expectation_args["result_format"]

            result_format = parse_result_format(result_format)
            
            lines=self.readlines() #Read in file lines

            # FIXME temporary fix for missing/ignored value
#            if func.__name__ in ['expect_column_values_to_not_be_null', 'expect_column_values_to_be_null']:
#                ignore_values = []



            # FIXME rename to mapped_ignore_values?
#            if len(ignore_values) == 0:
#                boolean_mapped_null_values = np.array([False for value in series])
#            else:
#                boolean_mapped_null_values = np.array([True if (value in ignore_values) or (pd.isnull(value)) else False
#                                                       for value in series])
            
            
            #Skip k initial lines designated by the user
            if skip is not None:
                try:
                    assert float(skip).is_integer()
                    assert float(skip) >= 0
                except:
                    raise ValueError("skip must be a positive integer")
                    
                for i in range(1,skip+1):
                    lines.pop(0)
                    
            null_lines = re.compile("\s+") #Ignore lines with just white space
            boolean_mapped_null_lines=np.array([bool(null_lines.match(line)) for line in lines])
            

            element_count = int(len(lines))

            # FIXME rename nonnull to non_ignored?
            nonnull_lines = lines[boolean_mapped_null_lines==False]
            nonnull_count = int((boolean_mapped_null_lines==False).sum())

            boolean_mapped_success_lines = func(self, nonnull_lines, *args, **kwargs)
            success_count = np.count_nonzero(boolean_mapped_success_lines)

            unexpected_list = list(nonnull_values[boolean_mapped_success_lines==False])
            unexpected_index_list = list(nonnull_values[boolean_mapped_success_lines==False].index)

            #success, percent_success = self._calc_map_expectation_success(success_count, nonnull_count, mostly)
            
            
        if nonnull_count > 0:
            
            percent_success = success_count / nonnull_count

            if mostly != None:
                success = bool(percent_success >= mostly)

            else:
                success = bool(nonnull_count-success_count == 0)

        else:
            success = True
            percent_success = None
            

            return_obj = self._format_column_map_output(
                result_format, success,
                element_count, nonnull_count,
                unexpected_list, unexpected_index_list
            )

            # FIXME Temp fix for result format
#            if func.__name__ in ['expect_column_values_to_not_be_null', 'expect_column_values_to_be_null']:
#                del return_obj['result']['unexpected_percent_nonmissing']
#                try:
#                    del return_obj['result']['partial_unexpected_counts']
#                except KeyError:
#                    pass

            return return_obj

        inner_wrapper.__name__ = func.__name__
        inner_wrapper.__doc__ = func.__doc__

        return inner_wrapper
    
    
class FileDataset(MetaFileDataset,file):
    """
    FileDataset instantiates the great_expectations Expectations API as a subclass of a python file object.
    For the full API reference, please see :func:`Dataset <great_expectations.Dataset.base.Dataset>`
    """

    # We may want to expand or alter support for subclassing dataframes in the future:
    # See http://pandas.pydata.org/pandas-docs/stable/extending.html#extending-subclassing-pandas

    @property
    def _constructor(self):
        return self.__class__

    def __finalize__(self, other, method=None, **kwargs):
        if isinstance(other, FileDataset):
            self._initialize_expectations(other.get_expectations_config(
                discard_failed_expectations=False,
                discard_result_format_kwargs=False,
                discard_include_configs_kwargs=False,
                discard_catch_exceptions_kwargs=False))
            # If other was coerced to be a PandasDataset (e.g. via _constructor call during self.copy() operation)
            # then it may not have discard_subset_failing_expectations set. Default to self value
            self.discard_subset_failing_expectations = getattr(other, "discard_subset_failing_expectations",
                                                               self.discard_subset_failing_expectations)
            if self.discard_subset_failing_expectations:
                self.discard_failing_expectations()
        super(FileDataset, self).__finalize__(other, method, **kwargs)
        return self

    def __init__(self, *args, **kwargs):
        super(FileDataset, self).__init__(*args, **kwargs)
        self.discard_subset_failing_expectations = kwargs.get('discard_subset_failing_expectations', False)
        
      

    
    
    
    
        
    
    
    
