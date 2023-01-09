# S3B
Easier S3 browser for CLI

- Enjoy the feeling like classic file system on AWS S3
- Support `ls`, `cd`, `mkdir`, `rm`
- Of course you can `download` and `upload` files

## Install

```shell script
pip install .
```

## How to use
run
```shell script
s3b
```
to use `default` profile, or
```shell script
s3b YOUR-PROFILE-NAME
```

Example usage
```shell script

S3 Browser - github.com/replon/s3b
============================================
Connecting to S3 using...
  profile_name: default
  aws_access_key_id: xxxxx
  aws_secret_access_key: xxxxx

Your bucket list
  [0] my.app
  [1] my.awesome.data
  [2] my.awesome.secret
  [3] special.bucket

select bucket(0-3): 0
============================================

(5 items)
  css                                 <dir>
  fonts                               <dir>
  js                                  <dir>
  favicon.ico                        4.2 KB     2020-11-20 20:21:14+00:00
  index.html                         1.2 KB     2020-11-20 20:21:14+00:00

<my.app> ~/$
<my.app> ~/$ ?

  commands : cd, l=ls, mkdir, rm, up=upload, down=download, q=exit

<my.app> ~/$ cd css
<my.app> ~/css/$

(2 items)
  app.css                            34.0 B     2020-11-20 20:21:14+00:00
  other.css                        449.6 KB     2020-11-20 20:21:15+00:00

<my.app> ~/css/$ down *.css
downloading 2 matched files
 [SUCCESS] done!

<my.app> ~/css/$ !ls
app.css    other.css

<my.app> ~/css/$ q

Bye :)

```
## Where to store my AWS information?
Make sure you have `credentials` file for accessing to AWS. If you don't have one, create one. 
- In linux or mac : `~/.aws/credentials`
- In Windows : `C://Users/USER_NAME/.aws/credentials`

And write in following format and save.

```text
[default]
aws_access_key_id = xxxxx
aws_secret_access_key = xxxxx
[profile2]
aws_access_key_id = xxxxx
aws_secret_access_key = xxxxx
```
That's all!

## Updates

- (0.1.0) First version, support basic features
- (0.1.1) Turn off color font in Windows, add setup scripts
- (0.1.2) Speed up by removal of full scanning


## Future works (Not supported yet)

- `mv` : move files
- `download -r` : recursive download
