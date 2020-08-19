### Engineering

> Avoid merge commits. Every commit is a story which makes a history (a linear one!).

> Not only the code, the discussions and approach are all as important and to be written
> down.

#### It all starts with a Pull Request (PR)

An effective way to make a change to the project is to make a proposal in
the form of a pull request against the `master` branch. Start with a small changeset
and add `[WIP]` tag to the PR and ask for preliminary review at first to decide upon the
correct direction.

Note: PR is also called Patch, Change List (CL), or Merge Request (MR).

#### PR descriptions

> A PR or commit description is a public record of **what** change is being made and **why**
> it was made.

Future:
1. Developers search for the commit based on its description.
2. Someone in the future looking for your change because of a faint memory of its relevance.
3. If all important information is in the code and not the description, it will be hard to
the commit

##### First Line

1. Short summary of what the changeset does.
2. Complete sentence, crafted as though it was an order.
    - an imperative sentence
    - No need to write the rest of the description as an imperative though.
3. Follow by  empty line.

Examples:

##### Body

This is normally the description.

1. A brief description of the problem being solved.
2. Why this is the best approach.
3. Shortcomings to the approached, if any (important!).

Additional info
4. background information
   - bug numbers
   - benchmark results
   - links to design documents
5. Include enough context for
   - reviewers
   - future readers to understand the Changes.

##### Good CL descriptions

Functionality change

Refactoring

Small Changeset still needs some context

##### Adapt the description before apply to the master

The PRs undergo changes during the review. It can be worthwhile to
review a PR (or commit) description, to ensure the description still
reflects what the PR (or commit) does.

##### Code authoring and review practices

Let us follow the same guide used by Apache Spark and Google Engineering teams.
see https://google.github.io/eng-practices.

##### Refactoring (code or documentation)

On any given day we work on the code and parallely modify the previously working code
for better maintenance and internal structure which we normally call as refactoring.

> What is *Refactoring*?
>
> It is a disciplined technique for restructuring an existing body of code, altering its
> internal structure without changing its external behaviour.

Resource link: https://refactoring.com/

##### Keep informed

As a par of a full distributed organization (i.e., people in different timezones), it is
important to stay informed about engineering-led initiatives.


##### Meeting

Schedule a meeting (via Google Meet) at 

https://calendar.google.com/calendar/b/1?cid=cGhpM2pjZGZlMDRpMHJtbGMzc2JpcDQ2OGtAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ

(1:1 15 min - 20 min (max.) - on demand

1. Stick to the agenda
2. If they can be discussed via mail, that would be good.
3. Make sure to share a google doc for meet.

(Group meet) 15 min - 20 min (max.) - on demand

1. Stick to the agenda.
2. Make sure to share a google doc for meet.

