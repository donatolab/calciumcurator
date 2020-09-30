from typing import Union

import numpy as np


class ContourManager:
    def __init__(
        self,
        im_shape: tuple,
        contours: list = [],
        initial_state: Union[str, np.ndarray] = "good",
        mode: str = 'all',
    ):
        self._contours = contours
        self._contour_labels = np.arange(1, len(contours) + 1)
        self._im_shape = im_shape

        if isinstance(initial_state, str):
            if initial_state == "good":
                self._good_contour = np.ones((len(contours),), dtype=np.bool)
            else:
                self._good_contour = np.zeros((len(contours),), dtype=np.bool)
        elif isinstance(initial_state, np.ndarray):
            self._good_contour = initial_state
        else:
            raise TypeError("initial_state should be a string or numpy array")

        self._selected_contours = {}
        self.mode = mode

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, mode: str):
        self._mode = mode

    @property
    def contours(self) -> list:
        return self._contours

    @contours.setter
    def contours(self, contours: list):
        self._contours = contours

    @property
    def good_contour(self) -> np.ndarray:
        return self._good_contour

    @good_contour.setter
    def good_contour(self, good_contour):
        self._good_contour = good_contour

    @property
    def accepted_contours(self) -> list:
        good_contour_indices = np.argwhere(self.good_contour)
        return [self.contours[i[0]] for i in good_contour_indices]

    @property
    def rejected_contours(self) -> list:
        bad_contour_indices = np.argwhere(np.logical_not(self.good_contour))
        return [self.contours[i[0]] for i in bad_contour_indices]

    @property
    def selected_contours(self) -> set:
        return self._selected_contours

    @selected_contours.setter
    def selected_contours(
        self, selected_contours: Union[list, np.ndarray, set]
    ):
        self._selected_contours = set(selected_contours)

    def make_accepted_mask(self):
        accepted_contours_image = np.zeros(self._im_shape, dtype=np.uint16)
        if self.mode == 'all':
            labels = self._contour_labels[self.good_contour]
            accepted_contours = self.accepted_contours

        elif self.mode == 'focus':
            selected_contours = np.array(list(self.selected_contours))
            accepted_contour_indices = np.argwhere(self.good_contour)
            selected_accepted = np.intersect1d(
                selected_contours,
                accepted_contour_indices,
                return_indices=False,
            )
            labels = self._contour_labels[selected_accepted]
            accepted_contours = [self.contours[i] for i in selected_accepted]

        for label, cont in zip(labels, accepted_contours):
            accepted_contours_image[
                np.round(cont[:, 0]).astype("int"),
                np.round(cont[:, 1]).astype("int"),
            ] = label

        return accepted_contours_image

    def make_rejected_mask(self):
        rejected_contours_image = np.zeros(self._im_shape, dtype=np.uint16)
        if self.mode == 'all':
            labels = self._contour_labels[np.logical_not(self.good_contour)]
            rejected_contours = self.rejected_contours
        elif self.mode == 'focus':
            selected_contours = np.array(list(self.selected_contours))
            rejected_contour_indices = np.argwhere(
                np.logical_not(self.good_contour)
            )
            selected_rejected = np.intersect1d(
                selected_contours,
                rejected_contour_indices,
                return_indices=False,
            )
            labels = self._contour_labels[selected_rejected]
            rejected_contours = [self.contours[i] for i in selected_rejected]

        for label, cont in zip(labels, rejected_contours):
            rejected_contours_image[
                np.round(cont[:, 0]).astype("int"),
                np.round(cont[:, 1]).astype("int"),
            ] = label

        return rejected_contours_image
