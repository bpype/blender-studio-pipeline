# SVN Set-Up

## Install/Setup SVN 
The Blender Studio Pipeline relies on SVN to version control all .blend files used in production. This guide will show you how to install an SVN on a workstation, assuming you already have an SVN server setup. To learn more about how to setup an SVN server visit the [SVN Documentation](https://subversion.apache.org/quick-start#setting-up-a-local-repo)
### Linux/Mac
1. Install SVN Client on your system via the [SVN Documentation](https://subversion.apache.org/packages.html)
2. Use the following command to checkout the current SVN repository into the SVN directory.
```bash
svn checkout http://your_svn.url ~/data/your_project_name/svn
```


### Windows
1. Download & Install the [TortoiseSVN Client](https://tortoisesvn.net/downloads.html)
2. Navigate to your project's root directory. Right-Click Select the `svn` folder and select `SVN Checkout`
3. Enter the URL to checkout under `URL of repository`  
4. Select OK to begin checking out the repository

![Tortoise SVN Checkout Dialogue Box](/media/td-guide/Tortoise_SVN_Checkout.jpg)

## Committing Changes to Repository

### Linux/Mac
To commit changes to the SVN use the following command. For more details see the [SVN Documentation](https://subversion.apache.org/quick-start#committing-changes)
```bash
svn commit -m "My Descriptive Log Message"
```

### Windows
To commit changes from the TortoiseSVN client, follow the steps below. For more information see the [TortoiseSVN Documentation](https://tortoisesvn.net/docs/release/TortoiseSVN_en/tsvn-dug-commit.html)

1. Navigate to your project's root directory. 
2. Right-Click Select the `svn` folder and select `SVN Commit`
3. Enter your commit's message in the box labelled `Message`
4. Review what files have changed in the box labelled `Changes made`

::: info Note 
For more details on how to set-up an SVN repository please see the official [SVN Documentation](https://subversion.apache.org/quick-start) and the [TortoiseSVN Documentation](https://tortoisesvn.net/docs/release/TortoiseSVN_en/tsvn-repository.html)
:::
