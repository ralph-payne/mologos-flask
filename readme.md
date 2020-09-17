## Mologos Project Description
- Flask Web application that allows users to find definitions of words and then upload their own example sentences containing the defined word
- The app tests users to remember the words by rendering the users' example sentences with the defined word missing
- Users then guess defined word and the application stores the progress of the user's learning
- Word definitions are provided by Merriam-Webster's Dictionary API


## The Challenge Page
q) How does the algorithm for the Challenge page work?
a) You tell us how important the word is (by assigning it a star or an unwatch). The algorithm takes that data and, along with the statistics of past performances, will give each word a certain weighting. This weighting determines the likelihood that you will see the word on the challenge page

### The Challenge Page Algorithm
1. Back end asks db for a list of users words (The words which the user does not want to appear are filtered out in the db query)
2. The words are stored in a list (List 1)
3. The random function is used to select a word
4. Once selected, the word is deleted from List 1 so that it cannot be chosen again
5. The example sentence containing the word is sliced up & the first half and the second half are assigned to a dictionary which is appended to List 2
6. Repeat Steps 1-5 until list 2 contains 5 words 
(note: In a future version, the algorithm will assign a certain weighting to each word so that there is a higher probability that "starred words" or words which the user frequently fails to remember are prioritised

## Technologies used
- Python / Flask
- JavaScript
- HTML5
- Bootstrap


## Wed 16 Sep - Plan
the plan for Wed 16 Sep is to create a homepage for Mologos
You will need
- a Mologos logo
- an idea of what the page will look like

Try to do something similar to the NewsGrid website
Use CSS Grid

Take one step at a time

1. Navbar
2. Showcase
3. ??
4. Footer

Make the homepage mobile responsive and add notes about how responsive it is
i.e. on the Navbar, the logo and the links stack
on the Footer, all the boxes stack


## Fri 18 Sep
Create Edit page
Make the submit button go next to the search input on the navbar
Change the classes so that it is clear which page you are on (navbar icons light up according to the page)
Remove green and red background from the tables#
Bring in the logo in the footer on the bottom left
