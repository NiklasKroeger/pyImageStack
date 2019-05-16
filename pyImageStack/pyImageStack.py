#!/usr/bin/env python3
__author__ = "Niklas Kroeger"
__email__ = "niklas@kroeger.dev"
__status__ = "Development"

import numpy as np
import tables


class ImageStack(object):
    """
    Image stack class that stores data in a pytables table (hdf5 file format)
    """
    def __init__(self, filename, dummy_img=None, metadata_cls=None, mode='r'):
        """
        Create a new ImageStack based on PyTables EArray

        This class opens the hdf5 file given by filename. If an img is given,
        an existing file is overwritten with a new file. The ImageStack is
        saved in a PyTables EArray, which can be indexed the same way as numpy
        arrays. The shape of the ImageStack is (N, *img.shape),
        where N is the number of images in the stack.

        Parameters
        ----------
        filename : str
            path to the h5 file the image stack should be saved in or from
            which the stack should be loaded

        dummy_img : numpy.ndarray or None
            If None the file under filename is opened. If data should be saved
            instead, the img should be an example image having the same shape
            and dtype as the images that should be stored. This template image
            is NOT stored. Images that should be saved have to be added with
            self.addImage(img)

        metadata_cls : dict
            A dict containing keys under which the desired metadata should be
            saved. The corresponding values should describe the columns datatype
            that should be stored. The datatype definition should be an instance
            of a pytables Col object. This can be used to define a new table
            layout (names and datatypes for columns) in order to save some
            metadata connected to the recorded images. This can be something
            like the exposure time of the recorded image, some light intensity
            value or a timestamp at which the image was recorded. This allows
            keeping the image and information about the acquisition together in
            a single file.
            Links for further reading:
            - https://www.pytables.org/usersguide/introduction.html
            - https://www.pytables.org/usersguide/datatypes.html

        mode : str
            Mode with which filename is opened. Defaults to 'r' for read
            access to the given file. If img is not None, the mode is instead
            set to 'w' for write access. This overwrites a possibly existing
            file with the same filename! If new images should be added to an
            existing ImageStack, 'a' can be tried. This also creates a new
            file if it does not yet exist
        """
        self.filename = filename
        self.mode = mode
        if dummy_img is not None:
            # create new image stack. This overwrites existing files!
            self.mode = 'w'
            self.atom = tables.Atom.from_dtype(dummy_img.dtype)

        self._h5file = tables.open_file(filename=self.filename,
                                        mode=self.mode)
        if dummy_img is not None:
            # create new image stack in given file
            self.data = self._h5file.create_earray(self._h5file.root,
                                                   'img_stack',
                                                   self.atom,
                                                   (0,) + dummy_img.shape)

            if metadata_cls is not None:
                self.metadata = self._h5file.create_table(self._h5file.root,
                                                          'metadata',
                                                          metadata_cls)
            else:
                self.metadata = None
        else:
            # load the images from the given file
            self.data = self._h5file.root.img_stack
            try:
                self.metadata = self._h5file.root.metadata
            except tables.exceptions.NoSuchNodeError as e:
                self.metadata = None

    @property
    def shape(self):
        return self.data.shape

    def add_image(self, img, metadata=None):
        """
        Add a new image to the stack

        Parameters
        ----------
        img : numpy.ndarray
            Image that should be added to the stack. Has to have the same
            shape and dtype as the template image that was passed during
            initialization of the ImageStack instance

        metadata : dict
            The metadata that should be saved alongside the image data. Note
            that the data type of the values passed here has to match that given
            at construction time of the ImageStack!
        """
        self.data.append(np.expand_dims(img, 0))
        if metadata is not None:
            row = self._get_metadata_row()
            for (key, value) in metadata.items():
                row[key] = value
            row.append()

    def has_metadata(self):
        """
        Quick way to check if this image stack makes use of the metadata
        feature.

        Returns
        -------
        bool
            True if there is metadata in this ImageStack. False if there is no
            metadata
        """
        return isinstance(self.metadata, tables.table.Table)

    def _get_metadata_row(self):
        """
        Get the current row of the metadata table. This is necessary to add a
        metadata entry.

        The variable returned by this method is the one you should use to append
        new metadata entries. This can be done by simply indexing it like a dict
        with the keys corresponding to the fields that were defined in the
        metadata_cls during initialization of this ImageStack instance. After
        filling all fields with the desired data remember to call row.append()
        to actually add the data to the table.

        Returns
        -------
        tables.tableextension.Row
            The metadata_table row.
        """
        if self.has_metadata():
            return self.metadata.row
        else:
            return None

    def __iter__(self):
        return self.data.__iter__()

    def __getitem__(self, item):
        return self.data.__getitem__(item)

    def __del__(self):
        if self.has_metadata() and self.metadata._v_isopen:
            self.metadata.flush()
        self._h5file.close()

if __name__ == '__main__':
    # Example usage:
    # Creating a new stack to save images:
    img_shape = (100, 200)  # the shape of our images is (100, 200)
    dummy_img = np.random.rand(*img_shape)

    # Optional: Definition of the metadata that should be saved along the images
    # Note that the data type for each field has to be defined here!
    metadata = {'exp_time': tables.Int32Col(),
                'some_string': tables.StringCol(itemsize=20)}

    # Create a new image stack to save some files. Note that the input img
    # for the constructor is not saved! See Docstring for more complete
    # explanation
    stack_write = ImageStack(filename='test_stack.h5',  # h5-file for the stack
                             dummy_img=dummy_img,  # sample image that defines our image shape
                             metadata_cls=metadata, # Optional metadata definition
                             )

    # Now we can append new images to this stack.
    for i in range(10):
        # we can now overwrite the initial metadata dict with actual data
        metadata['exp_time'] = i
        metadata['some_string'] = str(i)*(i+1)
        stack_write.add_image(np.random.rand(*img_shape),   # random image
                              metadata,  # and some pseudo metadata (optional)
                              )

    # the images are automatically saved. To close the file simply destroy the
    # stack instance
    del stack_write

    print('-'*50)
    # Reading an existing image stack:
    stack_read = ImageStack(filename='test_stack.h5')
    # Note image shape. First value is number of images (see Docstring for details)
    print(stack_read.shape)

    # to iterate over all images:
    for i, img in enumerate(stack_read):
        print(img.sum())
        if stack_read.has_metadata():
            print(stack_read.metadata[i])
