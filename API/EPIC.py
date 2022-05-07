"""
Script Name - EPIC.py

Purpose - Download the EPIC (Earth Polychromatic Imaging Camera) image(s).
For full API documentation - https://epic.gsfc.nasa.gov/about/api.

Created by Michael Samelsohn, 07/05/22
"""

# Imports #
import os

from NASA_API import NASA_API, get_request, download_image_url
from Utilities import Settings
from Utilities.Logging import Logger

# Logger #
log = Logger(module=os.path.basename(__file__), file_name=None)


def reformat_images_url(image_date):
    """
    Extract the date and time to later form the correct image URL.

    :param image_date: The date of the image (from the request response dictionary).
    :return: Tuple of year, month and date of the image.
    """

    log.debug("Extracting date and time information for image URL")
    date_and_time = image_date.split(" ")
    date_only = date_and_time[0].split("-")
    year = date_only[0]
    month = date_only[1]
    day = date_only[2]
    return year, month, day


class EPIC(NASA_API):
    def __init__(self, image_directory, number_of_images=Settings.EPIC_NUMBER_OF_PHOTOS_TO_COLLECT):
        """
        :param image_directory: The directory where the image is to be saved at.
        :param number_of_images: Number of images to collect.
        """

        super().__init__(image_directory)

        self.__number_of_images = number_of_images
        self.__check_number_of_images_value()

    def __check_number_of_images_value(self):
        """
        Check that number of images value is of an integer instance.
        If not, set to default value.
        """

        log.debug(f"Number of images is - {self.__number_of_images}")
        if not isinstance(self.__number_of_images, int):
            log.error("Number of images must be an int value, will reset to default")
            self.__number_of_images = Settings.EPIC_NUMBER_OF_PHOTOS_TO_COLLECT
            return
        if self.__number_of_images < 1:
            log.error("Number of images must be a positive integer value, will reset to default")
            self.__number_of_images = Settings.EPIC_NUMBER_OF_PHOTOS_TO_COLLECT
            return

    @property
    def number_of_images(self):
        """
        Get the number of images.
        :return: The number of images.
        """
        return self.__number_of_images

    @number_of_images.setter
    def number_of_images(self, new_number_of_images):
        """
        Set the number of images.
        :param new_number_of_images: The new number of images.
        """
        self.__number_of_images = new_number_of_images
        self.__check_number_of_images_value()

    def log_class_parameters(self):
        super().log_class_parameters()
        log.debug(f"The selected number of images is - {self.__number_of_images}")

    def earth_polychromatic_imaging_camera(self):
        """
        Save EPIC image(s) in the selected directory.
        Note - The images are saved as .png files.
        """

        log.debug("Retrieving EPIC (Earth Polychromatic Imaging Camera) image(s)")

        # Perform the API request.
        json_object = get_request(url=f"{Settings.EPIC_URL_PREFIX}{Settings.EPIC_URL_SUFFIX}")
        if json_object is None:  # API request failed.
            log.error("Check logs for more information on the failed API request")
            return

        # Process the response information.
        image_url_list = self.__process_response_information(response_information=json_object)

        # Download and save the image(s) to the relevant directory.
        download_image_url(api_type="EPIC", image_url=image_url_list)

    def __process_response_information(self, response_information):
        """
        Process the response information to extract the image URLs.

        :param response_information: The response (containing the relevant information) from the API request.
        :return: List of the image URLs.
        """

        if self.__number_of_images > len(response_information):
            log.warning(f"Selected number of images, {self.__number_of_images}, "
                        f"is more than the actual amount - {len(response_information)}")
        image_url_list = []
        for i in range(0, min(self.__number_of_images, len(response_information))):
            log.debug("Current image number is - {}".format(i + 1))
            image = response_information[i]
            image_id = image["image"]
            year, month, day = reformat_images_url(image["date"])
            image_url_list.append(Settings.EPIC_URL_PREFIX + "archive/natural/" + year + "/" + month + "/" + day +
                                  "/png/" + image_id + ".png")

        return image_url_list


if __name__ == "__main__":
    obj = EPIC(image_directory="", number_of_images=0)
    obj.log_class_parameters()
    obj.earth_polychromatic_imaging_camera()
