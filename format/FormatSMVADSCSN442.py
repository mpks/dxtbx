"""
An implementation of the SMV image reader for ADSC images. Inherits from
FormatSMVADSC, customised for example on ALS beamline 8.3.1 from back in the
day which had it's own way of recording beam centre.
"""

from __future__ import absolute_import, division, print_function

from dxtbx.format.FormatSMVADSCSN import FormatSMVADSCSN


class FormatSMVADSCSN442(FormatSMVADSCSN):
    """A class for reading SMV format ADSC images, and correctly constructing
    a model for the experiment from this, for instrument number 442."""

    @staticmethod
    def understand(image_file):
        """Check to see if this is ADSC SN 442."""

        # check this is detector serial number 442

        size, header = FormatSMVADSCSN.get_smv_header(image_file)

        return int(header["DETECTOR_SN"]) == 442

    def _detector(self):
        """Return a model for a simple detector, presuming no one has
        one of these on a two-theta stage. Assert that the beam centre is
        provided in the Mosflm coordinate frame."""

        distance = float(self._header_dictionary["DISTANCE"])
        beam_x = float(self._header_dictionary["DENZO_X_BEAM"])
        beam_y = float(self._header_dictionary["DENZO_Y_BEAM"])
        pixel_size = float(self._header_dictionary["PIXEL_SIZE"])
        image_size = (
            float(self._header_dictionary["SIZE1"]),
            float(self._header_dictionary["SIZE2"]),
        )
        trusted_range = self._adsc_trusted_range(pedestal=40)

        return self._detector_factory.simple(
            "CCD",
            distance,
            (beam_y, beam_x),
            "+x",
            "-y",
            (pixel_size, pixel_size),
            image_size,
            trusted_range,
            [],
            gain=self._adsc_module_gain(),
            pedestal=40,
        )

    def get_raw_data(self):
        """Get the pixel intensities (i.e. read the image and return as a
        flex array of integers.)"""

        assert len(self.get_detector()) == 1
        panel = self.get_detector()[0]
        image_size = panel.get_image_size()
        return self._get_endianic_raw_data(size=image_size)
