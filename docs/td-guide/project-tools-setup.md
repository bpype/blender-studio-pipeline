# Project Tools Setup

## Introduction

In this guide, you will learn how to setup the Blender Studio Pipeline, the backbone of [Blender Open Movies](https://studio.blender.org/films/). This workflow relies on Blender, some Blender Add-Ons, and additional services like [Kitsu](https://www.cg-wire.com/kitsu) and [Flamenco](https://flamenco.blender.org/). Wether you are an individual with a single computer or a studio with a full network of workstations, this guide offers a straightforward approach to set up the pipeline, complete with easy-to-follow examples. 

::: info Python Requirement
Running these scripts requires python 3.11+, please ensure [python & it's dependencies are installed](/td-guide/python.md) on your system before running blender with the below instructions
:::

## Creating Root Folder
To make this guide simple, we will assume we are working within the system's **homefolder**. To create a new directory in your homefolder please follow the below steps.

```bash
mkdir ~/data # Linux/Mac
```
```bash
mkdir %HOMEPATH%\data # Windows
```