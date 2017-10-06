##uniencode

A script to unify file encodings when multiple encodings are 
included in a file or change from one encoding to another. 

Tested with: Python 2.7

## Examples:

  - Change file from detected encoding(s) to utf-8
  
  ```bash
  python uniencode.py myfile
  ```
  - Change file encoding to iso-8859-7
  
  ```bash
  python uniencode.py myfile -e iso-8859-7
  ```

  - Change all text files under directory to utf-8

  ```bash
  python uniencode.py -r mydir
  ```

  - Change all *.srt files under a directory to utf-8

  ```bash
  python uniencode.py -r mydir -p *.srt
  ```
## Run tests

  ```bash
  python uniencode.py --test
  ```
