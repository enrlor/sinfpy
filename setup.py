from distutils.core import setup
setup(
  name = 'sinfpy',         # How you named your package folder (MyLib)
  packages = ['sinfpy'],   # Chose the same as "name"
  version = '0.2.5',      # Start with a small number and increase it with every change you make
  license='GNU GPLv3',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description = 'Algorithm to compute semantic influence scores in dynamic graphs.',   # Give a short description about your library
  author = 'enrlor',                   # Type in your name
  author_email = 'enricaloria94@gmail.com',      # Type in your E-Mail
  url = 'https://github.com/enrlor/sinfpy',   # Provide either the link to your github or to your website
  download_url = 'https://github.com/enrlor/sinfpy/releases/tag/v_0.2.5',   
  keywords = ['sna', 'graph', 'influence', 'game analytics'],   # Keywords that define your package best
  install_requires=[
        'numpy',
        'pandas',
        'ray',
        'psutil',
        'scipy'
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Programming Language :: Python :: 3',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'Intended Audience :: Education',
    'Topic :: Scientific/Engineering',
    'Topic :: Scientific/Engineering :: Mathematics',
    'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
  ],
)