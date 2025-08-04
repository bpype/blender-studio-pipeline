# Introduction
In this guide, you will learn how to set up the Blender Studio Pipeline, the backbone of [Blender Open Movies](https://studio.blender.org/films/). This workflow relies on Blender, several Blender add-ons, and additional services like [Kitsu](https://www.cg-wire.com/kitsu) and [Flamenco](https://flamenco.blender.org/). Whether you are an individual with a single computer or a studio with a full network of workstations, this guide offers a straightforward approach to setting up the pipeline, complete with easy-to-follow examples.

::: info Python Requirement
Running these scripts requires Python 3.11 or higher. Please ensure that [Python and its dependencies are installed](/td-guide/python.md) on your system before running Blender with the instructions below.
:::

<br/><br/>

# Infrastructure
Description of the infrastructure used at Blender Studio.

## Workstations
Artists at Blender Studio use Linux workstations, running Gentoo Linux. While the infrastructure is designed to support other operating systems, it is primarily intended for a heterogeneous environment where every machine is set up in a similar way.

Artist workstations also serve as clients for the render farm.

* [**Reference manual**](/gentoo/user/introduction.md)
* [**Setup guide**](/gentoo/td/overview.md)

## Shared Storage
We use two shared drives:

* `/render` to store render farm output
* `/shared` to store project and shared data

## Version Control System
We use SVN. While it presents a higher barrier to entry, it offers a robust and efficient way to store and version large binary files during production.

This means we need an SVN service (which can be on the LAN or online).

## Network/Web Services

* Syncthing (needs access to `/shared`)
* Flamenco (**render farm** needs access to `/shared` and `/render`)
* Kitsu (**production tracker** can be hosted anywhere)
* Watchtower (needs access to Kitsu)

## Other Dependencies

We rely on the [Blender Buildbot](https://builder.blender.org) infrastructure to provide Blender builds to the workstations.
