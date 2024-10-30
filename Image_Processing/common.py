"""
Script Name - common.py

Purpose - Commonly used functions.

Created by Michael Samelsohn, 12/05/22
"""

# Imports #
import copy
import math
import numpy as np
from numpy import ndarray, random
from Settings import image_settings
from Utilities.decorators import measure_runtime
from Settings.settings import log


def convert_to_grayscale(image: ndarray) -> ndarray:
    """
    Convert a color image to grayscale.
    The RGB values are converted to grayscale using the NTSC formula: 0.299 ∙ Red + 0.587 ∙ Green + 0.114 ∙ Blue.
    This formula closely represents the average person's relative perception of the brightness of red, green, and blue
    light.

    :param image: Color image for conversion. If image is grayscale, it is returned as is.

    :return: Grayscale image.
    """

    log.info("Converting image to grayscale")

    log.debug("Checking image shape")
    if len(image.shape) == 3:
        log.debug("Extracting the red, green and blue images")
        red, green, blue = image[:, :, 0], image[:, :, 1], image[:, :, 2]
        log.debug("Performing the conversion")
        grayscale_image = 0.2989 * red + 0.5870 * green + 0.1140 * blue
        return grayscale_image
    else:
        log.warning("Image is already grayscale, returning as is")
        return image


def salt_and_pepper(image: ndarray, pepper=0.001, salt=0.001) -> ndarray:
    """
    Add salt and pepper (white and black) pixels to an image at random.

    :param image: The image for distortion.
    :param pepper: Percentage of black pixels to be randomized into the image.
    :param salt: Percentage of white pixels to be randomized into the image.

    :return: Distorted image.
    """

    log.info("Adding salt and pepper to the image")

    pepper_pixels, salt_pixels = 0, 0  # Counters for the salt and pepper pixels.
    noisy_image = np.zeros(shape=image.shape)
    for row in range(image.shape[0]):
        for col in range(image.shape[1]):
            # Randomizing the new pixel value according to the following three options - salt, pepper, unchanged.
            new_pixel = random.choice([0, 1, image[row][col]], p=[pepper, salt, 1 - (pepper + salt)])

            # Checking that pixel wasn't already pepper (black).
            if new_pixel == 0 and image[row][col] != 0:
                pepper_pixels += 1  # Incrementing salt counter.
            # Checking that pixel wasn't already salt (white).
            if new_pixel == 1 and image[row][col] != 1:
                salt_pixels += 1  # Incrementing salt counter.
            # Setting the new pixel value.
            noisy_image[row][col] = new_pixel

    log.info(
        f"Pepper pixels - {pepper_pixels} ({round(100 * pepper_pixels / (image.shape[0] * image.shape[1]), 2)}% of "
        f"total pixels)")
    log.info(
        f"Salt pixels - {salt_pixels} ({round(100 * salt_pixels / (image.shape[0] * image.shape[1]), 2)}% of "
        f"total pixels)")

    return noisy_image


def use_lookup_table(image, lookup_table: ndarray | list) -> ndarray:
    """
    Convert image using lookup table values.
    The lookup table provides a transformation value for each possible intensity value (normally, 0-255).
    Lookup tables are extremely time-efficient when it comes to pixel-wise (as opposed to neighbourhood) transformations
    where there is a formula for each intensity value -> O(1).
    Otherwise, the calculation is done for every pixel -> O(N*M) (N, M are the image dimensions).

    :param image: The image to be used for the lookup table.
    :param lookup_table: The lookup table.
    :return: Result image where every pixel was transformed according to its corresponding index value in the lookup
    table.
    """

    log.info("Applying lookup table to the image")

    new_image = copy.deepcopy(image)  # Deep copy, so the original is not altered.
    new_image[:, :] = lookup_table[image[:, :]]
    return new_image


def scale_pixel_values(scale_factor=image_settings.DEFAULT_SCALING_FACTOR):
    def wrapper(func):
        def inner(*args, **kwargs):
            kwargs["image"] = scale_image(image=kwargs["image"], scale_factor=scale_factor)
            return_image = func(*args, **kwargs)
            return scale_image(image=return_image, scale_factor=1 / scale_factor)

        return inner

    return wrapper


def scale_image(image: ndarray, scale_factor=image_settings.DEFAULT_SCALING_FACTOR) -> ndarray:
    """
    Scale the pixel values of an image by the provided scaling factor.
    This function is useful when the pixel range is [0, 1] and it needs to be converted to integer values (scaling
    upwards by 255) and vice-versa.

    :param image: The image to be scaled.
    :param scale_factor: The scaling factor.
    Note - For scaling factor 255, the image is also set as int type (rather than float).

    :return: Scaled image.
    """

    log.info(f"Scaling the image by a factor of {scale_factor}")

    scaled_image = copy.deepcopy(image * scale_factor)  # Deep copy, so the original is not altered.

    if scale_factor == 255:
        log.debug("Scale factor is 255 -> Setting the image as int type")
        scaled_image = scaled_image.astype(int)

    return scaled_image


def calculate_histogram(image: ndarray, normalize=image_settings.DEFAULT_HISTOGRAM_NORMALIZATION) \
        -> tuple[ndarray, ndarray, ndarray] | ndarray:
    """
    Calculate the histogram of an image. A histogram shows the amount of pixels per pixel intensity value.
    If the histogram is normalized, it shows the probabilities per pixel intensity value.
    Note - if the image is a color one, the return value will contain three histograms (one for each color channel).

    :param image: The image.
    :param normalize: Boolean value indicating if the histogram is to be normalized or not.

    :return: Histogram of the provided image.
    """

    log.info("Calculating histogram of an image")

    if len(image.shape) == 3:
        log.debug("Color image -> Splitting the image to its three channels")

        log.debug("Extracting the red, green and blue images")
        red, green, blue = image[:, :, 0], image[:, :, 1], image[:, :, 2]
        return calculate_histogram(image=red, normalize=normalize), \
            calculate_histogram(image=green, normalize=normalize), \
            calculate_histogram(image=blue, normalize=normalize)

    log.debug("Scaling the image to have a histogram with integer values")
    image = scale_image(image=image, scale_factor=255)

    log.debug("Performing the histogram calculation")
    histogram = np.zeros(256)
    for row in range(image.shape[0]):
        for col in range(image.shape[1]):
            histogram[image[row][col]] += 1  # Incrementing the counter for the current pixel value.

    if normalize:
        log.debug("Normalizing the histogram (converting to probabilities per pixel intensity value)")
        histogram /= (image.shape[0] * image.shape[1])

    return histogram


def generate_filter(filter_type=image_settings.DEFAULT_FILTER_TYPE, filter_size=image_settings.DEFAULT_FILTER_SIZE,
                    **kwargs) -> ndarray:
    """
    Types of filters:
        * Box filter - An all ones filter (with normalization).
        * Gaussian filter - TODO: Explain the principle behind the construction of the filter (formula 3-46 in page 167).

    :param filter_type: The type of filter to be generated.
    :param filter_size: The size of the filter to be generated. Can be either an integer or a tuple of integers.

    :return: Matrix array with the specified dimensions and based on the selected filter type.
    """

    log.info(f"Generating filter of type, {filter_type} with size {filter_size}")

    # Asserting that filter size is an odd number and is symmetrical.
    filter_size_square = 1
    if isinstance(filter_size, int):
        if filter_size % 2 == 0:
            log.raise_exception(message="Filter size is an even number. Filters should be odd number size",
                                exception=ValueError)
        else:  # Selected filter size is odd.
            # Setting the shape of the filter to be symmetrical.
            filter_size_square = (filter_size, filter_size)

    log.debug("Identifying the filter type and generating it")
    kernel_matrix = np.zeros(shape=filter_size_square)
    try:
        match filter_type:
            case image_settings.BOX_FILTER:
                log.debug("Box type filter selected")
                kernel_matrix = np.ones(shape=filter_size_square)
                kernel_matrix /= np.sum(kernel_matrix)  # Normalize.
            case image_settings.GAUSSIAN_FILTER:
                log.debug("Gaussian type filter selected with parameters:")
                log.debug(f"k = {kwargs["k"]}")
                log.debug(f"sigma = {kwargs["sigma"]}")
                center_position = filter_size // 2
                for row in range(filter_size):
                    for col in range(filter_size):
                        r_squared = math.pow(row - center_position, 2) + math.pow(col - center_position, 2)
                        kernel_matrix[row][col] = kwargs["k"] * math.exp(
                            -r_squared / (2 * math.pow(kwargs["sigma"], 2)))
                kernel_matrix /= np.sum(kernel_matrix)  # Normalize.
    except KeyError:
        log.raise_exception("Missing arguments for filter generation", exception=KeyError)

    return kernel_matrix


def pad_image(image: ndarray, padding_type=image_settings.DEFAULT_PADDING_TYPE,
              padding_size=image_settings.DEFAULT_PADDING_SIZE) -> ndarray:
    """
    Padding the image boundaries.

    :param image: The image for padding.
    :param padding_type: The padding type.
    Types of padding methods:
        * Zero padding ("zero_padding") - Add zeros to the boundaries.
        TODO: Add more padding types (mirror, boundary extension).
    :param padding_size: The padding size.

    :return: Padded image.
    """

    log.info(f"Padding image boundaries with {padding_type} (size={padding_size}) method")

    log.debug("Calculating the new row and col values")
    rows = image.shape[0] + 2 * padding_size
    cols = image.shape[1] + 2 * padding_size

    log.debug("Identifying the padding type and applying it")
    padded_image = np.zeros(shape=(rows, cols, 3)) if len(image.shape) == 3 else np.zeros(shape=(rows, cols))
    match padding_type:
        case image_settings.ZERO_PADDING:
            log.debug("Zero padding selected")
            padded_image[padding_size:-padding_size, padding_size:-padding_size] = image[:, :]

    return padded_image


@measure_runtime
def convolution_2d(image: ndarray, kernel: ndarray, padding_type=image_settings.DEFAULT_PADDING_TYPE,
                   normalization_method=image_settings.DEFAULT_NORMALIZATION_METHOD) -> ndarray:
    """
    Perform convolution on an image with a kernel matrix. Mainly used for spatial filtering.

    :param image: The image to be convolved.
    :param kernel: Kernel matrix.
    :param padding_type: The padding type used for extending the image boundaries.
    :param normalization_method: Preferred normalization method for the convoluted image. Options are - unchanged,
    stretch and cutoff.

    :return: Convolution of the image with the convolution object.
    """

    log.info("Performing 2D convolution on the image")

    log.debug("Asserting that kernel is symmetrical")
    kernel_size = kernel.shape[0]  # TODO: Make sure this is correct.
    if kernel.shape[0] != kernel.shape[1]:
        log.raise_exception(message="Kernel is not symmetrical", exception=ValueError)

    # Padding the image so the kernel can be applied to the image boundaries.
    padded_image = pad_image(image=image, padding_type=padding_type, padding_size=kernel_size // 2)

    log.debug("Performing the convolution between the padded image and the kernel matrix")
    convolution_image = np.zeros(shape=image.shape)
    for row in range(kernel_size // 2, image.shape[0] + kernel_size // 2):
        for col in range(kernel_size // 2, image.shape[1] + kernel_size // 2):
            # Extract the sub-image.
            sub_image = extract_sub_image(image=padded_image, position=(row, col), sub_image_size=kernel_size)
            # Perform the convolution for the sub-image.
            convolution_image[row - kernel_size // 2, col - kernel_size // 2] = [
                np.sum(sub_image[:, :, 0] * kernel),
                np.sum(sub_image[:, :, 1] * kernel),
                np.sum(sub_image[:, :, 2] * kernel)] if len(image.shape) == 3 else np.sum(sub_image * kernel)

    return image_normalization(image=convolution_image, normalization_method=normalization_method)


def image_normalization(image: ndarray, normalization_method=image_settings.DEFAULT_NORMALIZATION_METHOD) \
        -> ndarray:
    """
    Normalize image according to one of the following methods:
    • unchanged - Image remains as is. In this case, there might be values exceeding the expected image range of [0, 1].
    • stretch - The pixel values are compressed or stretched to the boundaries of 0 and 1. This means that the lowest
      pixel value turns to 0 and the highest turns to 1. The rest are linearly distributed between them.
    • cutoff - Eliminate all values exceeding the range of [0, 1]. This means that pixel values below 0, become 0, and
      pixel values above 1, become 1.

    :param image: The image for normalization.
    :param normalization_method: The normalization method (as mentioned in the description above).

    :return: Normalized image.
    """

    log.info(f"Normalizing image according to the following method - {normalization_method}")

    match normalization_method:
        case 'unchanged':
            log.debug("Retuning image as is")
            log.warning("Image might contain pixel values exceeding the range of [0, 1]")
            return image
        case 'stretch':
            # Stretching the image contrast to range [0, 1].
            return contrast_stretching(image=image)
        case 'cutoff':
            log.debug("'Cutting' values above 1 or below 0")
            image[image > 1] = 1
            image[image < 0] = 0
            log.warning("Image might lose information due to this normalization method")
            return image
        case _:
            log.error(f"Normalization method, {normalization_method}, is not a recognized option")
            log.error("Available options are - unchanged, stretch, cutoff (read convolution_2d (part of common.py) "
                      "docstring for a better understanding as to what each method does)")
            log.warning("Will use default method - unchanged")
            return image


def extract_sub_image(image: ndarray, position: tuple[int, int], sub_image_size: int) -> ndarray:
    """
    Extract sub-image from an image. Mainly used for performing neighbourhood operations.

    :param image: The image.
    :param position: The x,y position of the center pixel (of the sub-image).
    :param sub_image_size: The size of the sub-image.

    :return: Sub-image, where the center pixel is based on the selected position.
    """

    # Asserting that sub-image size is an odd number (so it can have a center pixel).
    if sub_image_size % 2 == 0:
        log.raise_exception(message="The selected sub image is an even integer (sub image must have a center pixel, "
                                    "therefore, its size must be an odd integer)", exception=ValueError)

    # Setting the positions for the rows.
    row_start = position[0] - (sub_image_size // 2)
    row_end = position[0] + (sub_image_size // 2) + 1

    # Setting the positions for the cols.
    col_start = position[1] - (sub_image_size // 2)
    col_end = position[1] + (sub_image_size // 2) + 1

    # Extracting the sub image.
    sub_image = image[row_start:row_end, col_start:col_end]

    return sub_image


def contrast_stretching(image: ndarray) -> ndarray:
    """
    Perform contrast stretching on an image. Contrast stretching is useful only when the image has values which are
    outside the normal range [0, 1]. This normally happens when performing high-pass filtering (image sharpening).

    :param image: The image for contrast stretching.
    :return: Image with pixels values stretched to range [0, 1].
    """

    log.info("Stretching the contrast of the image to the range of [0, 1]")

    log.debug("Calculating the min/max values found in the image")
    max_value = np.max(image)
    log.debug(f"Maximum value is - {max_value}")
    min_value = np.min(image)
    log.debug(f"Minimum value is - {min_value}")

    log.debug("Calculating the slope")
    m = 1 / (max_value - min_value)
    log.debug(f"Slope is - {m}")

    log.warning("Assuming that the normal pixel value range for the image is - [0, 1] "
                "(apply the scale_image function if not)")
    return m * (image[:, :] - min_value)
