# Getting started

## TL;DR

1. Login
1. Create container page
1. Create form page in container page
1. Define form
1. Publish

## Overview

This form builder allows you to create web forms. No HTML or programming knowledge is required for this. The Form Builder works on a web page basis, therefore a form corresponds to a page, hereafter called "form page". These form pages are created in a hierarchical page structure, with only three levels: 

1. root level to distinguish the language versions.
1. container level for grouping form pages, e.g. for assigning authorizations
1. form pages

Form pages contain a page title, the form or the fields of a form, some mail settings and an (optional) captcha. The individual form fields, field types, field names, etc. are compiled by the user. 

A published form can be reached under its published URL in the standard design of the form builder ("standalone form page"), but can also be queried without the standard design via the URL parameter `url?embed=true`. This second variant can be used, for example, as an iFrame on an existing page.
