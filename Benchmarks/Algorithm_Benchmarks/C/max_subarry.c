#include<stdio.h>
#include<limits.h>
#include <string.h>
#include <assert.h>     /// for assert
#include <stdbool.h>    /// for bool
#include <stdio.h>      /// for IO operations
#include <stdlib.h>     /// for dynammic memory allocation

static int kadane(int Array[], int n) {
  int max_sum = 0;
  int current_sum = 0;

  for(int i=0; i<n; i++) {
    current_sum = current_sum + Array[i];
    if (current_sum < 0)
      current_sum = 0; 
    if(max_sum < current_sum)
      max_sum = current_sum; 
  }
  return max_sum;
}

int n = 97;

/** Driver Code */
int main(int argc, const char *argv[]) {
    
    int *numbers;

    numbers = malloc(n * sizeof(*numbers));

    for (int i=0; i<n; i++) {
        scanf("%d", &numbers[i]);
    }

    int size = 30000000;

    int k = 0;

    /* Intializes random number generator */
    for (int i = 0; i < size; i++) {

         k = kadane(numbers, n);

    }
    return 0;
}