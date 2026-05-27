/* This coursework specification, and the example code provided during the
 * course, is Copyright 2024 Heriot-Watt University.
 * Distributing this coursework specification or your solution to it outside
 * the university is academic misconduct and a violation of copyright law. */

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef unsigned char u_char;

/* The RGB values of a pixel. */
struct Pixel {
    u_char red;
    u_char green;
    u_char blue;
};

/* An image loaded from a file. */
struct Image {
    int width;
    int height;
    struct Pixel *arr;
};

/* Free a struct Image */
void free_image(struct Image *img)
{   
    if (img == NULL) {
        return; /* already free */
    }
    free(img->arr);
    free(img);
}

/* Opens and reads an image file, returning a pointer to a new struct Image.
 * On error, prints an error message and returns NULL. */
struct Image *load_image(const char *filename)
{
    /* Open the file for reading */
    FILE *f = fopen(filename, "r");
    if (f == NULL) {
        fprintf(stderr, "File %s could not be opened.\n", filename);
        return NULL;
    }

    /* Allocate the Image object, and read the image from the file */
    struct Pixel* pArr;
    int width;
    int height;
    char type[4];
    u_char r, g, b;
    int i = 0;
    if (fscanf(f, "%s %d %d ", type, &width, &height) != 3) {
        fprintf(stderr, "File %s has wrong file format.\n", filename);
        return NULL;
    }
    if (strcmp(type, "HS8") != 0) { /* Not a HS8 file*/
        fprintf(stderr, "File %s has wrong file format.\n", filename);
        return NULL;
    }
    if (width < 1 ||  height < 1) { /* Too Small */
        fprintf(stderr, "File %s has too small picture.\n", filename);
        return NULL;
    }

    pArr = (struct Pixel*) calloc(width * height, sizeof(struct Pixel)); /*Initialise a pixel array*/
    if (pArr == NULL) {
        fprintf(stderr, "Out of Memory");
        return NULL;
    }
    while (fscanf(f, "%c%c%c", &r, &b, &g) && i < width * height) {
        pArr[i].red = r;
        pArr[i].green = g;
        pArr[i].blue = b;
        i += 1; /*Move pointer on pixel array*/
    }
    if (i != width * height) { /* Incorrect size specified */
        fprintf(stderr, "File %s has wrong file format.\n", filename);
        return NULL;
    }

    /* Question 2b */
    struct Image* img = (struct Image*) malloc(sizeof(struct Image));
    img->width = width;
    img->height = height;
    img->arr = pArr;
    
    /* Close the file */
    fclose(f);

    if (img == NULL) {
        fprintf(stderr, "File %s could not be read.\n", filename);
        return NULL;
    }

    return img;
}

/* Write img to file filename. Return true on success, false on error. */
bool save_image(const struct Image *img, const char *filename)
{
    /* TODO: Question 2c */
    FILE* f;

    /* Open a file for writing and clearing */
    f = fopen(filename, "w");

    if (f == NULL) {
        fprintf(stderr, "File %s could not be opened.\n", filename);
        return false;
    }

    fprintf(f, "HS8 %d %d ", img->width, img->height);
    /* Close the file */
    fclose(f);
    /* Open a file for appending */
    f = fopen(filename, "a");

    if (f == NULL) {
        fprintf(stderr, "File %s could not be opened.\n", filename);
        return false;
    }

    for (int i = 0; i < img->width * img->height; i++) {
        fprintf(f, "%c%c%c", img->arr[i].red, img->arr[i].green, img->arr[i].blue);
    }

    /* Close the file */
    fclose(f);
    return true;
}

/* Allocate a new struct Image and copy an existing struct Image's contents
 * into it. On error, returns NULL. */
struct Image *copy_image(const struct Image *source)
{
    /* Question 2d */
    struct Image* img = (struct Image*) malloc(sizeof(struct Image));
    if (img == NULL) {
        fprintf(stderr, "Out of memory\n");
        return NULL; // Memory allocation failed
    }
    img->width = source->width;
    img->height = source->height;
    img->arr = (struct Pixel*)calloc(source->width * source->height, sizeof(struct Pixel)); /*Initialise a pixel array*/

    if (img->arr == NULL) {
        fprintf(stderr, "Out of memory\n");
        return NULL; // Memory allocation failed
    }

    for (int i = 0; i < source->width * source->height; i++) {
        img->arr[i].red = source->arr[i].red;
        img->arr[i].green = source->arr[i].green;
        img->arr[i].blue = source->arr[i].blue;
    }
    return img;
}

/* Perform your first task.
 * (TODO: Write a better comment here, and rename the function.
 * You may need to add or change arguments depending on the task.)
 * Returns a new struct Image containing the result, or NULL on error. */
struct Image *apply_MONO(const struct Image *source)
{
    /* TODO: Question 3 */
    struct Image* img = copy_image(source);
    if (img == NULL) {
        return NULL;
    }
    for (int i = 0; i < source->width * source->height; i++) {
        u_char gray = (u_char)(0.299 * img->arr[i].red + 0.587 * img->arr[i].green + 0.114 * img->arr[i].blue);
        img->arr[i].red = gray;
        img->arr[i].green = gray;
        img->arr[i].blue = gray;
    }
    return img;
}

/* Perform your second task.
 * Computes the number of identical pixels and different pixels
 * between 2 Image objects.
 * Returns true on success, or false on error. */
bool apply_COMP(const struct Image *source, const struct Image* other)
{
    /* Question 4 */
    int idenPix = 0;
    /* Compare every pixel in image 1 to every pixel in image 2 and vice versa. If identical pixel found, break to ignore duplicates. */
    for (int i = 0; i < source->width * source->height; i++) {
        for (int j = 0; j < other->width * other->height; j++) {
            if (source->arr[i].red == other->arr[j].red
                && source->arr[i].green == other->arr[j].green
                && source->arr[i].blue == other->arr[j].blue) {
                idenPix += 1;
                break; /* Ignore duplicates */
            }
        }
    }
    for (int i = 0; i < other->width * other->height; i++) {
        for (int j = 0; j < source->width * source->height; j++) {
            if (other->arr[i].red == source->arr[j].red 
                && other->arr[i].green == source->arr[j].green 
                && other->arr[i].blue == source->arr[j].blue) {
                idenPix += 1;
                break; /* Ignore duplicates */
            }
        }
    }
    int diffPix = source->width * source->height + other->width * other->height - idenPix;
    printf("Identical pixels : %d \nDifferent pixels %d \n", idenPix, diffPix);
    return true;
}

int main(int argc, char *argv[])
{

    /* Check command-line arguments 
    If there are less then 4 or an odd number, terminate.*/
    if (argc < 4 || argc % 2 != 0) {
        fprintf(stderr, "Usage: process REFERENCEFILE INPUTFILE OUTPUTFILE (...INPUTFILE OUTPUTFILE)\n");
        return 1;
    }


    /* Reserve space for all images (input and output)*/
    struct Image** IArr = (struct Image**)calloc((argc - 2), sizeof(struct Image*));
    if (IArr == NULL) {
        fprintf(stderr, "Out of memory\n");
        return 1; // Memory allocation failed
    }

    /* Load the input images */
    for (int i = 2; i < argc; i += 2) {
        IArr[i-2] = load_image(argv[i]);

        if (IArr[i - 2] == NULL) {
            for (int j = 0; j < argc - 2; j++) { /* Free every image */
                free_image(IArr[j]);
            }
            free(IArr);
            return 1;
        }
    }
    /* Apply the first process */
    for (int i = 2; i < argc; i += 2) {
        IArr[i - 1] = apply_MONO(IArr[i - 2]);

        if (IArr[i - 1] == NULL) {
            fprintf(stderr, "First process failed.\n");
            for (int j = 0; j < argc - 2; j++) { /* Free every image */
                free_image(IArr[j]);
            }
            free(IArr);
            return 1;        }
        }
    struct Image* ref_img = load_image(argv[1]);
    if (ref_img == NULL) {
        return 1;
    }

    /* Apply the second process and Save the output image */
    for (int i = 2; i < argc; i += 2) {
        if (!apply_COMP(IArr[i - 1], ref_img)) {

            fprintf(stderr, "Second process failed.\n");
            for (int j = 0; j < argc - 2; j++) { /* Free every image */
                free_image(IArr[j]);
            }
            free(IArr);
            free_image(ref_img);
            return 1;
        }
        if (!save_image(IArr[i - 1], argv[i+1])) {

            fprintf(stderr, "Saving image to %s failed.\n", argv[3]);
            for (int j = 0; j < argc - 2; j++) { /* Free every image */
                free_image(IArr[j]);
            }
            free(IArr);
            free_image(ref_img);
            return 1;
        }
    }



    for (int j = 0; j < argc - 2; j++) { /* Free every image */
        free_image(IArr[j]);
    }
    free(IArr);
    free_image(ref_img);
    return 0;
}
